# Whois Child Mention Checker

This script processes a JSON file containing messages to identify and extract details of senders who mention children (under 18) in messages tagged with the `#whois` hashtag. It utilizes OpenAI's GPT-3.5-turbo model to analyze message content and outputs the results to a text file.

## Requirements

- `openai==0.28.0`
- Python 3.7 or higher

### Installation

To install the required packages, run:

```bash
pip install -r requirements.txt
```

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key.

## Usage

1. Ensure the `input_data.json` file is in the same directory or provide the correct path.
2. Set the `OPENAI_API_KEY` environment variable before running the script.

### Example

```bash
export OPENAI_API_KEY='your-api-key-here'
python whois_child_mention_checker.py
```

## Output

The results are saved in `output_results.txt`, containing the sender details and timestamps of messages that mention children under the `#whois` hashtag.

**Author: [Sergei Poluektov](https://github.com/seregatipich/)**
