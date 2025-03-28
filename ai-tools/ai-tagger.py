import os
import json
import re
from typing import List, Dict, Any, Set, Optional
import requests
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import yaml
from collections import defaultdict


class AdvancedObsidianProcessor:
    def __init__(
        self,
        vault_path: str,
        config_path: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        embedding_model: Optional[str] = None,
        similarity_threshold: float = 0.5,
        verbose: bool = False,
    ):
        """
        Advanced Obsidian Document Processor with backlinks, tags, and advanced analysis

        :param vault_path: Path to Obsidian vault
        :param config_path: Optional path to configuration YAML file
        :param api_key: Optional Anthropic API key
        :param model: Optional Anthropic model name
        :param embedding_model: Optional embedding model name
        :param similarity_threshold: Threshold for document similarity (0.0-1.0)
        :param verbose: Enable verbose logging
        """
        # Configure logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        self.logger = logging.getLogger("ObsidianTagger")

        # Load configuration from file if provided
        config = {}
        if config_path:
            try:
                with open(config_path, "r") as config_file:
                    config = yaml.safe_load(config_file)
                self.logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                self.logger.warning(f"Failed to load config file: {e}")

        # Set parameters with priority: direct args > config file > defaults
        self.vault_path = vault_path
        self.api_key = api_key or config.get("anthropic_api_key", "")
        self.model = model or config.get("model", "claude-3-5-sonnet-20241022")
        self.similarity_threshold = similarity_threshold

        # Initialize embedding model for semantic analysis
        embedding_model_name = embedding_model or config.get(
            "embedding_model", "all-MiniLM-L6-v2"
        )
        self.logger.info(f"Loading sentence embedding model: {embedding_model_name}")
        self.embedding_model = SentenceTransformer(embedding_model_name)

        # Ensure vault path exists
        if not os.path.exists(self.vault_path):
            raise ValueError(f"Vault path {self.vault_path} does not exist")

        # Knowledge graph to track document relationships
        self.knowledge_graph = {}
        self.backlinks = {}

        # Tag management
        self.document_tags = {}  # Store tags for each document
        self.tag_clusters = defaultdict(set)  # Group similar documents by tag
        self.global_tag_map = {}  # Map content signatures to consistent tags

    def read_markdown_files(self) -> List[Dict[str, str]]:
        """
        Read all markdown files in the vault

        :return: List of dictionaries with file info
        """
        markdown_files = []
        self.logger.info(f"Scanning for markdown files in {self.vault_path}")

        try:
            for root, _, files in tqdm(
                os.walk(self.vault_path), desc="Discovering Markdown Files"
            ):
                for file in files:
                    if file.endswith(".md"):
                        full_path = os.path.join(root, file)
                        try:
                            with open(full_path, "r", encoding="utf-8") as f:
                                content = f.read()
                                markdown_files.append(
                                    {
                                        "filename": file,
                                        "path": full_path,
                                        "content": content,
                                    }
                                )
                        except Exception as e:
                            self.logger.warning(f"Failed to read {full_path}: {e}")

            self.logger.info(f"Found {len(markdown_files)} markdown files")
            return markdown_files
        except Exception as e:
            self.logger.error(f"Error scanning vault: {e}")
            return []

    def extract_existing_links(self, content: str) -> List[str]:
        """
        Extract existing links from markdown content

        :param content: Document content
        :return: List of existing links
        """
        # Extract links in various markdown formats
        link_patterns = [
            r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]",  # Obsidian wiki-style links with optional alias
            r"\[([^\]]+)\]\(([^\)]+)\)",  # Markdown standard links
        ]

        existing_links = []
        for pattern in link_patterns:
            matches = re.findall(pattern, content)

            # Handle different match formats
            for match in matches:
                if isinstance(match, tuple):
                    # For standard markdown links, use the URL part
                    if len(match) > 1:
                        existing_links.append(match[1])  # URL part
                    existing_links.append(match[0])  # Text part
                else:
                    existing_links.append(match)

        # Debug output
        if existing_links:
            print(f"Found existing links: {existing_links}")

        return existing_links

    def extract_existing_tags(self, content: str) -> Set[str]:
        """
        Extract existing Obsidian tags from markdown content

        :param content: Document content
        :return: Set of existing tags (without the # symbol)
        """
        # Extract Obsidian tags (both inline and YAML frontmatter)
        tags = set()

        # Extract inline tags (#tag format, but not within code blocks)
        # Split content by code blocks first
        code_block_pattern = r"```.*?```"
        content_parts = re.split(code_block_pattern, content, flags=re.DOTALL)

        # Process non-code parts
        for part in content_parts[::2]:  # Skip code blocks (odd indices)
            # Find inline tags
            inline_tags = re.findall(r"(?<!\S)#([a-zA-Z0-9_/-]+)", part)
            tags.update(inline_tags)

        # Extract YAML frontmatter tags
        frontmatter_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            # Look for tags: or tag: in the frontmatter
            tag_lines = re.findall(r"tags?:\s*(.*?)(?:\n|$)", frontmatter)

            for line in tag_lines:
                # Handle array format: tags: [tag1, tag2]
                if "[" in line and "]" in line:
                    array_tags = re.findall(r"\[(.*?)\]", line)
                    if array_tags:
                        for tag_list in array_tags:
                            # Split by comma and clean up
                            for tag in tag_list.split(","):
                                clean_tag = tag.strip().strip("\"'")
                                if clean_tag:
                                    tags.add(clean_tag)
                # Handle YAML list format with dashes
                elif "-" in line:
                    yaml_tags = re.findall(r"-\s*([^\s,]+)", line)
                    tags.update(yaml_tags)
                # Handle simple format: tags: tag1 tag2
                else:
                    simple_tags = line.strip().split()
                    tags.update(simple_tags)

        # Debug output
        if tags:
            print(f"Found existing tags: {tags}")

        return tags

    def semantic_similarity_tagging(
        self, documents: List[Dict[str, str]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Compute semantic relationships between documents with comprehensive linking

        :param documents: List of documents
        :return: Dictionary of document similarities with link metadata
        """
        self.logger.info("Generating document embeddings...")
        # Generate embeddings for all documents
        embeddings = {}
        for doc in tqdm(documents, desc="Computing Embeddings"):
            embeddings[doc["filename"]] = self.embedding_model.encode(
                doc["content"][:1000]
            )

        # Compute pairwise similarities with detailed link information
        document_similarities = {}
        self.logger.info(
            f"Computing document similarities (threshold: {self.similarity_threshold})..."
        )

        total_similarities_found = 0

        for doc1 in tqdm(documents, desc="Semantic Linking"):
            similarities = []
            doc1_basename = os.path.basename(doc1["filename"])

            for doc2 in documents:
                if doc1["filename"] != doc2["filename"]:
                    # Compute similarity score
                    sim_score = np.dot(
                        embeddings[doc1["filename"]], embeddings[doc2["filename"]]
                    ) / (
                        np.linalg.norm(embeddings[doc1["filename"]])
                        * np.linalg.norm(embeddings[doc2["filename"]])
                    )

                    # Extract existing links to avoid duplicates
                    existing_links = self.extract_existing_links(doc1["content"])

                    # Normalize existing links and current filename for comparison
                    normalized_existing_links = [
                        os.path.basename(link) for link in existing_links
                    ]
                    doc2_basename = os.path.basename(doc2["filename"])

                    # Debug information
                    if sim_score > self.similarity_threshold:
                        self.logger.debug(
                            f"High similarity ({sim_score:.2f}) between: {doc1_basename} and {doc2_basename}"
                        )
                        if doc2_basename in normalized_existing_links:
                            self.logger.debug(
                                f"  - Skipping: {doc2_basename} already linked in {doc1_basename}"
                            )

                    # Add similar documents as potential links with improved filename comparison
                    if (
                        sim_score > self.similarity_threshold
                        and doc2_basename not in normalized_existing_links
                    ):
                        total_similarities_found += 1
                        similarities.append(
                            {
                                "filename": doc2["filename"],
                                "similarity_score": float(sim_score),
                                "suggested_link_text": self._generate_link_text(
                                    doc1, doc2
                                ),
                            }
                        )

            # Sort similarities by score in descending order
            document_similarities[doc1["filename"]] = sorted(
                similarities, key=lambda x: x["similarity_score"], reverse=True
            )

            # Debug output for each document
            self.logger.debug(
                f"Found {len(similarities)} similar documents for {doc1_basename}"
            )

        self.logger.info(
            f"Total similarities found across all documents: {total_similarities_found}"
        )
        return document_similarities

    def _generate_link_text(
        self, source_doc: Dict[str, str], target_doc: Dict[str, str]
    ) -> str:
        """
        Generate a contextual link text between two documents

        :param source_doc: Source document
        :param target_doc: Target document
        :return: Suggested link text
        """
        try:
            prompt = f"""Generate a concise, descriptive link text connecting these two documents:

            Source Document (Filename: {source_doc["filename"]}):
            Excerpt: {source_doc["content"][:500]}

            Target Document (Filename: {target_doc["filename"]}):
            Excerpt: {target_doc["content"][:500]}

            Provide a 3-5 word link text that captures the relationship:
            """

            return self._call_claude_api(prompt).strip()

        except Exception as e:
            print(f"Error generating link text: {e}")
            return f"Related: {target_doc['filename']}"

    def generate_backlinks(
        self,
        document_similarities: Dict[str, List[Dict[str, Any]]],
        documents: List[Dict[str, str]],
    ):
        """
        Generate bidirectional backlinks

        :param document_similarities: Semantic similarity results
        :param documents: List of all documents
        """
        print("Generating Backlinks...")
        self.backlinks = {}

        for doc in tqdm(documents, desc="Creating Backlinks"):
            filename = doc["filename"]

            # Initialize backlinks for this document
            self.backlinks[filename] = []

            # Find documents that link to this document
            for other_doc in documents:
                if other_doc["filename"] == filename:
                    continue

                # Check if this document appears in other document's similarities
                similar_docs = document_similarities.get(other_doc["filename"], [])
                relevant_links = [
                    link for link in similar_docs if link["filename"] == filename
                ]

                if relevant_links:
                    self.backlinks[filename].append(
                        {
                            "source_document": other_doc["filename"],
                            "link_text": relevant_links[0].get(
                                "suggested_link_text", "Related"
                            ),
                            "similarity_score": relevant_links[0].get(
                                "similarity_score", 0
                            ),
                        }
                    )

    def generate_tags(self, documents: List[Dict[str, str]]) -> Dict[str, List[str]]:
        """
        Generate consistent tags for documents based on content similarity

        :param documents: List of documents
        :return: Dictionary mapping document filenames to lists of tags
        """
        print("Analyzing documents for tag generation...")

        # First, extract existing tags from all documents
        for doc in tqdm(documents, desc="Extracting Existing Tags"):
            existing_tags = self.extract_existing_tags(doc["content"])
            self.document_tags[doc["filename"]] = list(existing_tags)

            # Add documents to tag clusters based on existing tags
            for tag in existing_tags:
                self.tag_clusters[tag].add(doc["filename"])

        # Generate embeddings for content-based tag suggestions
        print("Generating content embeddings for tag analysis...")
        content_embeddings = {}
        for doc in tqdm(documents, desc="Computing Content Embeddings"):
            # Use a larger chunk of content for better tag analysis
            content_embeddings[doc["filename"]] = self.embedding_model.encode(
                doc["content"][:2000]
            )

        # Group similar documents for consistent tagging
        similarity_groups = []
        processed_docs = set()

        print("Grouping similar documents for consistent tagging...")
        for doc1 in tqdm(documents, desc="Creating Tag Groups"):
            if doc1["filename"] in processed_docs:
                continue

            # Start a new group with this document
            current_group = [doc1["filename"]]
            processed_docs.add(doc1["filename"])

            # Find similar documents
            for doc2 in documents:
                if (
                    doc2["filename"] in processed_docs
                    or doc1["filename"] == doc2["filename"]
                ):
                    continue

                # Compute similarity score
                sim_score = np.dot(
                    content_embeddings[doc1["filename"]],
                    content_embeddings[doc2["filename"]],
                ) / (
                    np.linalg.norm(content_embeddings[doc1["filename"]])
                    * np.linalg.norm(content_embeddings[doc2["filename"]])
                )

                # If very similar, add to the same group
                if sim_score > 0.8:  # Higher threshold for tag consistency
                    current_group.append(doc2["filename"])
                    processed_docs.add(doc2["filename"])

            if len(current_group) > 1:
                similarity_groups.append(current_group)

        # Generate tags for each document
        print("Generating AI tags for documents...")
        for doc in tqdm(documents, desc="Generating Tags"):
            try:
                # Skip if we already have sufficient tags
                if len(self.document_tags.get(doc["filename"], [])) >= 5:
                    continue

                # Generate AI tags
                ai_tags = self._generate_document_tags(doc)

                # Ensure consistent tags across similar documents
                for group in similarity_groups:
                    if doc["filename"] in group:
                        # Share tags with the group
                        for filename in group:
                            if filename != doc["filename"]:
                                # Merge tags between similar documents
                                existing_group_tags = self.document_tags.get(
                                    filename, []
                                )
                                self.document_tags[filename] = list(
                                    set(existing_group_tags + ai_tags)
                                )

                # Add AI-generated tags to document's tags
                existing_tags = self.document_tags.get(doc["filename"], [])
                self.document_tags[doc["filename"]] = list(set(existing_tags + ai_tags))

            except Exception as e:
                print(f"Error generating tags for {doc['filename']}: {e}")

        return self.document_tags

    def _generate_document_tags(self, document: Dict[str, str]) -> List[str]:
        """
        Generate tags for a document using AI

        :param document: Document to generate tags for
        :return: List of generated tags
        """
        try:
            # First check if we can reuse existing tags from similar documents
            content_signature = document["content"][:100].lower()  # Simple signature
            if content_signature in self.global_tag_map:
                return self.global_tag_map[content_signature]

            # Generate tags using Claude API
            prompt = f"""Generate 3-5 relevant tags for this document in Obsidian format.
            
            Document Title: {document["filename"]}
            
            Document Content:
            {document["content"][:1500]}
            
            Rules for tags:
            1. Use lowercase words without spaces (e.g., #database, #system-design)
            2. Use hyphens for multi-word tags (e.g., #distributed-systems)
            3. Be specific but not too narrow
            4. Don't include the # symbol in your response
            5. Return only the tags separated by commas
            
            Tags:
            """

            response = self._call_claude_api(prompt).strip()

            # Process the response to extract tags
            # Remove any # symbols if present
            response = response.replace("#", "")

            # Split by commas and clean up
            tags = [tag.strip().lower() for tag in response.split(",")]

            # Filter out empty tags and ensure proper format
            tags = [re.sub(r"[^a-z0-9_/-]", "", tag) for tag in tags if tag]

            # Store in global map for consistency
            self.global_tag_map[content_signature] = tags

            return tags

        except Exception as e:
            print(f"Error in tag generation: {e}")
            # Return some generic tags as fallback
            return ["document", "note"]

    def process_vault(self, dry_run=False, tags_only=False, links_only=False):
        """
        Comprehensive vault processing workflow

        :param dry_run: If True, analyze but don't modify files
        :param tags_only: If True, only generate tags
        :param links_only: If True, only generate links
        :return: Dictionary with analysis results
        """
        # 1. Initial document processing
        self.logger.info(f"Starting Obsidian Vault Processing for {self.vault_path}...")
        markdown_files = self.read_markdown_files()

        if not markdown_files:
            self.logger.error("No markdown files found. Aborting.")
            return {}

        # 2. Semantic Similarity Analysis (skip if tags_only)
        document_similarities = {}
        if not tags_only:
            document_similarities = self.semantic_similarity_tagging(markdown_files)

        # 3. Generate Backlinks (skip if tags_only)
        if not tags_only:
            self.generate_backlinks(document_similarities, markdown_files)

        # 4. Generate Tags (skip if links_only)
        document_tags = {}
        if not links_only:
            document_tags = self.generate_tags(markdown_files)

        # 5. Update documents with generated links, backlinks, and tags
        if not dry_run:
            self.logger.info("Updating Documents...")
            self._update_documents(markdown_files, document_similarities)
        else:
            self.logger.info("Dry run mode - skipping document updates")

        self.logger.info("Vault Processing Complete!")
        return {
            "document_similarities": document_similarities,
            "backlinks": self.backlinks,
            "document_tags": document_tags,
        }

    def _update_documents(
        self,
        documents: List[Dict[str, str]],
        document_similarities: Dict[str, List[Dict[str, Any]]],
    ):
        """
        Update documents with generated links, backlinks, and tags

        :param documents: Original documents
        :param document_similarities: Semantic similarity results
        """
        for doc in tqdm(documents, desc="Updating Documents"):
            try:
                # Read original content
                with open(doc["path"], "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract existing tags to avoid duplicates
                existing_tags = self.extract_existing_tags(content)

                # Get AI-generated tags for this document
                ai_tags = self.document_tags.get(doc["filename"], [])

                # Combine existing and new tags, removing duplicates
                all_tags = list(existing_tags)
                for tag in ai_tags:
                    if tag not in existing_tags:
                        all_tags.append(tag)

                # Prepare to add new links
                new_links = document_similarities.get(doc["filename"], [])

                # Limit to top 3 suggested links
                new_links = new_links[:3]

                # Prepare link text
                link_texts = []
                for link in new_links:
                    link_text = link.get("suggested_link_text", link["filename"])
                    link_texts.append(f"[[{link['filename']}|{link_text}]]")

                # Add backlinks section if not exists
                backlink_section = "\n\n## Backlinks\n"
                backlinks = self.backlinks.get(doc["filename"], [])

                if backlinks:
                    backlink_section += "".join(
                        [
                            f"- [[{bl['source_document']}|{bl['link_text']}]]\n"
                            for bl in backlinks
                        ]
                    )

                # Check if the document has YAML frontmatter
                has_frontmatter = (
                    re.match(r"^---\s*\n.*?\n---", content, re.DOTALL) is not None
                )

                # If it has frontmatter, update the tags in the frontmatter
                if has_frontmatter:
                    # Extract the frontmatter
                    frontmatter_match = re.match(
                        r"^---\s*\n(.*?)\n---", content, re.DOTALL
                    )
                    if frontmatter_match:
                        frontmatter = frontmatter_match.group(1)
                        rest_of_content = content[frontmatter_match.end() :]

                        # Check if frontmatter already has tags
                        has_tags = re.search(r"tags?:", frontmatter) is not None

                        if has_tags:
                            # Replace existing tags
                            new_frontmatter = re.sub(
                                r"tags?:.*?(?=\n[^\s]|\n$|$)",
                                f"tags: {', '.join(all_tags)}",
                                frontmatter,
                                flags=re.DOTALL,
                            )
                        else:
                            # Add tags to frontmatter
                            new_frontmatter = (
                                frontmatter + f"\ntags: {', '.join(all_tags)}"
                            )

                        # Reconstruct the document
                        content = f"---\n{new_frontmatter}\n---{rest_of_content}"
                else:
                    # If no frontmatter, add tags at the top of the document
                    tag_section = " ".join([f"#{tag}" for tag in all_tags])
                    content = tag_section + "\n\n" + content

                # Add suggested links and backlinks
                if link_texts or backlinks:
                    # Suggested Links Section
                    if link_texts:
                        content += "\n\n## Suggested Related Documents\n"
                        content += "\n".join(link_texts)

                    # Add Backlinks Section
                    content += backlink_section

                # Write updated content
                with open(doc["path"], "w", encoding="utf-8") as f:
                    f.write(content)

            except Exception as e:
                print(f"Could not update {doc['filename']}: {e}")

    def _call_claude_api(self, prompt: str) -> str:
        """
        Call Claude API with a given prompt

        :param prompt: Prompt to send to Claude
        :return: API response
        """
        if not self.api_key:
            self.logger.warning("No API key provided, using placeholder text")
            return f"Related content for {prompt[:20]}..."

        try:
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
                "Anthropic-Version": "2023-06-01",
            }

            payload = {
                "model": self.model,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}],
            }

            self.logger.debug(f"Calling Claude API with model: {self.model}")
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                data=json.dumps(payload),
                timeout=30,  # Add timeout to prevent hanging
            )

            if response.status_code != 200:
                self.logger.error(
                    f"API call failed: {response.status_code} - {response.text}"
                )
                return f"Related content (API error)"

            return response.json()["content"][0]["text"]

        except Exception as e:
            self.logger.error(f"Error calling Claude API: {e}")
            return f"Related content (error: {str(e)[:50]})"


def setup_argparse():
    """Set up command line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Advanced Obsidian Vault Processor with AI tagging and linking",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("vault_path", help="Path to Obsidian vault directory")

    parser.add_argument("-c", "--config", help="Path to YAML configuration file")

    parser.add_argument(
        "-o",
        "--output",
        default="./obsidian_analysis",
        help="Output directory for analysis results",
    )

    parser.add_argument(
        "-k", "--api-key", help="Anthropic API key (overrides config file)"
    )

    parser.add_argument(
        "-m", "--model", help="Anthropic model name (overrides config file)"
    )

    parser.add_argument(
        "-e", "--embedding-model", help="Sentence transformer model for embeddings"
    )

    parser.add_argument(
        "-t",
        "--threshold",
        type=float,
        default=0.5,
        help="Similarity threshold (0.0-1.0)",
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Analyze without modifying files"
    )

    parser.add_argument(
        "--tags-only",
        action="store_true",
        help="Only generate tags, skip links and backlinks",
    )

    parser.add_argument(
        "--links-only", action="store_true", help="Only generate links, skip tags"
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    return parser


def main():
    """Main entry point for the CLI application"""
    parser = setup_argparse()
    args = parser.parse_args()

    # Create output directory if it doesn't exist
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Initialize processor
        processor = AdvancedObsidianProcessor(
            vault_path=args.vault_path,
            config_path=args.config,
            api_key=args.api_key,
            model=args.model,
            embedding_model=args.embedding_model,
            similarity_threshold=args.threshold,
            verbose=args.verbose,
        )

        # Process vault with appropriate options
        results = processor.process_vault(
            dry_run=args.dry_run, tags_only=args.tags_only, links_only=args.links_only
        )

        if not results:
            print("No results generated. Check logs for errors.")
            sys.exit(1)

        # Save results to JSON
        print(f"Saving analysis results to {output_dir}...")
        with open(
            output_dir / "obsidian_advanced_analysis.json", "w", encoding="utf-8"
        ) as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Save tags specifically for reference
        print("Saving tag analysis...")
        with open(output_dir / "obsidian_tags.json", "w", encoding="utf-8") as f:
            json.dump(results["document_tags"], f, indent=2, ensure_ascii=False)

        print("Processing complete!")

    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
