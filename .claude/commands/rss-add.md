---
name: rss-add
description: Add a new weekly item from an RSS feed URL using the rss-weekly-adder agent
arguments:
  - name: rss_url
    description: The RSS feed URL to add
    required: true
---

Use the rss-weekly-adder agent to add a new weekly item from the provided RSS feed URL: $rss_url

The agent will:
1. Parse the RSS feed to extract relevant information
2. Automatically identify the appropriate category or create a new one if needed
3. Create a new YAML file in the items directory with the feed information
4. Follow the repository's code architecture principles