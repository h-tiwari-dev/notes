# Obsidian AI Tagger (Cached Version)

An enhanced version of the Obsidian AI Tagger with advanced caching capabilities for improved performance and efficiency.

## Features

All the features of the original AI Tagger, plus:

- **Intelligent Caching**: Only processes files that have changed since the last run
- **Embedding Cache**: Stores and reuses document embeddings to reduce computation time
- **Tag Cache**: Remembers previously generated tags for consistent tagging
- **Similarity Cache**: Preserves document similarity calculations between runs
- **Force Refresh Option**: Ability to ignore cache and reprocess all files when needed
- **Cache Directory Configuration**: Customize where cache files are stored

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
python ai-tagger-cached.py /path/to/your/vault [options]
```

### Command Line Options

```
usage: ai-tagger-cached.py [-h] [-c CONFIG] [-o OUTPUT] [-k API_KEY] [-m MODEL]
                          [-e EMBEDDING_MODEL] [-t THRESHOLD] [--dry-run]
                          [--tags-only] [--links-only] [--no-cache]
                          [--cache-dir CACHE_DIR] [--force-refresh] [-v]
                          vault_path

Advanced Obsidian Vault Processor with AI tagging and linking

positional arguments:
  vault_path            Path to Obsidian vault directory

optional arguments:
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
  --no-cache            Disable caching (default: False)
  --cache-dir CACHE_DIR
                        Directory to store cache files (default: None)
  --force-refresh       Force refresh all files, ignoring cache (default: False)
  -v, --verbose         Enable verbose logging (default: False)
```

### Cache-Specific Options

- `--no-cache`: Disable the caching system entirely
- `--cache-dir CACHE_DIR`: Specify a custom directory for cache files
- `--force-refresh`: Ignore existing cache and process all files

### Configuration File

You can use a YAML configuration file to store settings, including cache configuration:

```yaml
# config.yaml
anthropic_api_key: "your-api-key-here"
model: "claude-3-5-sonnet-20241022"
embedding_model: "all-MiniLM-L6-v2"
cache_dir: "./.obsidian_cache"  # Custom cache directory
```

## Examples

### Basic Usage with Caching

```bash
# Process your vault with caching enabled (default)
python ai-tagger-cached.py ~/Documents/my-obsidian-vault
```

### Advanced Usage

```bash
# Disable caching
python ai-tagger-cached.py ~/Documents/my-obsidian-vault --no-cache

# Force refresh (ignore cache)
python ai-tagger-cached.py ~/Documents/my-obsidian-vault --force-refresh

# Specify custom cache directory
python ai-tagger-cached.py ~/Documents/my-obsidian-vault --cache-dir ./my-cache-folder

# Dry run with verbose output
python ai-tagger-cached.py ~/Documents/my-obsidian-vault --dry-run -v
```

## How Caching Works

1. **File Change Detection**: The tool creates and maintains hashes of your files to detect changes
2. **Skip Unchanged Files**: Files that haven't changed since the last run are skipped
3. **Embedding Cache**: Document embeddings are stored to avoid recomputing them
4. **Tag Cache**: Previously generated tags are stored for consistency
5. **Similarity Cache**: Document similarity calculations are preserved between runs

This caching system significantly improves performance for large vaults, especially when only a few files change between runs.

## Cache Structure

The cache is stored in the specified cache directory (defaults to `.obsidian_cache` in the parent directory of your vault) and includes:

- File metadata cache (hashes and timestamps)
- Embedding cache (document vectors)
- Tag cache (generated tags)
- Similarity cache (document relationships)

## Requirements

- Python 3.8+
- sentence-transformers
- numpy
- requests
- tqdm
- pyyaml
- pickle (for caching)

## License

MIT
