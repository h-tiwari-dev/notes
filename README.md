# Obsidian AI Tagger

An advanced CLI tool for automatically tagging, linking, and organizing your Obsidian vault using AI.

## Features

- **AI-Powered Tagging**: Automatically generates relevant tags for your notes
- **Semantic Linking**: Creates links between related documents based on content similarity
- **Backlink Generation**: Builds a network of backlinks to improve navigation
- **Content Analysis**: Uses embeddings to understand document relationships

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/obsidian-ai-tagger.git
cd obsidian-ai-tagger

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python ai-tagger.py /path/to/your/vault [options]
```

### Command Line Options

```
positional arguments:
  vault_path            Path to Obsidian vault directory

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to YAML configuration file (default: None)
  -o OUTPUT, --output OUTPUT
                        Output directory for analysis results (default: ./obsidian_analysis)
  -k API_KEY, --api-key API_KEY
                        Anthropic API key (overrides config file) (default: None)
  -m MODEL, --model MODEL
                        Anthropic model name (overrides config file) (default: None)
  -e EMBEDDING_MODEL, --embedding-model EMBEDDING_MODEL
                        Sentence transformer model for embeddings (default: None)
  -t THRESHOLD, --threshold THRESHOLD
                        Similarity threshold (0.0-1.0) (default: 0.5)
  --dry-run             Analyze without modifying files (default: False)
  --tags-only           Only generate tags, skip links and backlinks (default: False)
  --links-only          Only generate links, skip tags (default: False)
  -v, --verbose         Enable verbose logging (default: False)
```

### Configuration File

You can use a YAML configuration file to store settings:

```yaml
# config.yaml
anthropic_api_key: "your-api-key-here"
model: "claude-3-5-sonnet-20241022"
embedding_model: "all-MiniLM-L6-v2"
```

## Examples

### Basic Usage

```bash
# Process your vault with default settings
python ai-tagger.py ~/Documents/my-obsidian-vault
```

### Advanced Usage

```bash
# Dry run with verbose output
python ai-tagger.py ~/Documents/my-obsidian-vault --dry-run -v

# Only generate tags
python ai-tagger.py ~/Documents/my-obsidian-vault --tags-only

# Use a custom configuration and output directory
python ai-tagger.py ~/Documents/my-obsidian-vault -c my-config.yaml -o ./results

# Adjust similarity threshold
python ai-tagger.py ~/Documents/my-obsidian-vault -t 0.7
```

## Requirements

- Python 3.8+
- sentence-transformers
- numpy
- requests
- tqdm
- pyyaml

## License

MIT
