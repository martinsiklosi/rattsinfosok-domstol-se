# Proof of concept: Scraping rattsinfosok.domstol.se with Playwright

This is a proof of concept that [rattsinfosok.domstol.se](https://rattsinfosok.domstol.se/lagrummet/) can be scraped using Playwright, a browser automation tool. 
The script loads all court filing between two dates from a select court and saves the reports on the first page.

## Install dependencies

To run the script you need to install BeautifulSoup and Playwright

```
pip install beautifulsoup4
pip install playwright
playwright install
```