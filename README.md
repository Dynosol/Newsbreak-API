# NewsBreak API Publisher

An API for publishing articles to NewsBreak. This script handles the complete publishing workflow including draft creation, image upload, content updates, NLP metrics calculation, and final publication.

## Prerequisites

- Python 3.9+(?) newer is better
- Required Python packages (install via pip):
  ```bash
  pip install -r requirements.txt 
  ```

## Configuration

The script can be configured in three ways, in order of precedence:

1. Command-line arguments (highest priority)
2. JSON configuration file
3. Default values (lowest priority)

### Environment Variables

The script requires authentication cookies which should be set as environment variables. To set these up, create a `.env` file based on the provided `.env.example` file. You can do this by copying the example file and filling in the correct values. Find the auth cookies/headers you need for your specific organizations by:

1. Logging into your NewsBreak Contributor Platform.
2. Navigate to "Write an Article".
3. Open the browser console and navigate to "Network".
4. Type anything into the empty article content, then watch a `POST` request called `draft` be sent out.
5. Copy the headers and cookies directly, or you can also copy the cURL request that is sent out.
6. All done!

## Usage

### Basic Usage

```bash
python newsbreak_api.py --title "My Article Title" --content-file "article.txt"
```

### Using a Configuration File for uploading an article

Create a JSON configuration file (e.g., `config.json`):

```json
{
    "title": "My Article Title",
    "author_name": "John Doe",
    "author_url": "example.com",
    "article_credit": "Special Report",
    "content_file": "article.txt",
    "image_file": "image.jpg",
    "image_link": "https://example.com/image.jpg",
    "image_credit": "Photo by John Doe"
}
```

Then run:

```bash
python newsbreak_api.py --config config.json
```

### Using Command-line Arguments for uploading an article

| Argument | Description | Default Value |
|----------|-------------|---------------|
| `--title` | Article title | "Draft content..." |
| `--author-name` | Author's name | "Temp author" |
| `--author-url` | Author's URL | "harvard.edu" |
| `--article-credit` | Article byline/credit | "Temp byline..." |
| `--image-link` | URL of the image | Default NewsBreak image |
| `--image-credit` | Image credit text | "testing_credit!" |
| `--content-file` | Path to article content file | "./fake-content.txt" |
| `--image-file` | Path to image file to upload | "./crimson.jpg" |
| `--config` | Path to JSON config file | None |

## File Requirements

### Content File
- Plain text file containing the article content (markdown support incoming)
- UTF-8 encoded
- Must exist and not be empty

### Image File
- Supported formats: JPEG, PNG
- Must exist for upload purposes!! and be readable

## Publishing Process

The script performs the following steps:

1. Creates a draft article
2. Uploads the specified image
3. Updates the article content
4. Calculates NLP metrics
5. Publishes the article

## Example Commands

1. Basic usage with minimal parameters:
```bash
python newsbreak_api.py --title "Breaking News" --content-file "news.txt"
```

2. Full command-line configuration:
```bash
python newsbreak_api.py \
    --title "Breaking News" \
    --author-name "Jane Smith" \
    --author-url "newsorg.com" \
    --article-credit "Special Report" \
    --content-file "article.txt" \
    --image-file "photo.jpg" \
    --image-link "https://newsorg.com/photo.jpg" \
    --image-credit "Photo by Jane Smith"
```

3. Using a config file:
```bash
python newsbreak_api.py --config my_article_config.json
```

## Troubleshooting

Common issues and solutions:

1. **Session Expired**
   - Error: "Session expired - received HTML login page"
   - Solution: Refresh your authentication cookies

2. **File Not Found**
   - Error: "Content file not found" or "Could not find image file"
   - Solution: Verify file paths and permissions

3. **Empty Content**
   - Error: "Content file is empty"
   - Solution: Ensure your content file contains article text