from contextlib import contextmanager
import os

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


@contextmanager
def playwright_browser(headless: bool = True, slow_mo: float = 0):
    """A simple context manager for the playwright browser."""
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless, slow_mo=slow_mo)
    try:
        yield browser
    finally:
        browser.close()
        playwright.stop()


def get_frame(page):
    iframe_selector = "#lowerFrame > iframe"
    iframe_name = "LagrummetFrame2"
    page.wait_for_selector(iframe_selector)
    iframe = page.frame(name=iframe_name)
    assert iframe is not None
    return iframe


def load_results(iframe, court_value: str, start_date: str, end_date: str) -> None:
    """Load the results in the iframe.
    start_date and end_date must be in the format yyyy-mm-dd."""

    # Select all courts
    dropdown_selector = "#select-domstolmyndighet"
    iframe.wait_for_selector(dropdown_selector)
    iframe.select_option(dropdown_selector, court_value)

    # Enter start date
    start_date_selector = "#falt-avgorandedatum-fran"
    iframe.wait_for_selector(start_date_selector)
    iframe.fill(start_date_selector, start_date)

    # Enter end date
    end_date_selector = "body > form > div:nth-child(5) > div > div > div:nth-child(1) > div:nth-child(2) > input[type=text]:nth-child(3)"
    iframe.wait_for_selector(end_date_selector)
    iframe.fill(end_date_selector, end_date)

    # Press search
    search_button_selector = "body > form > div:nth-child(5) > div > div > div:nth-child(2) > div.formularKnappOmrade > button"
    iframe.wait_for_selector(search_button_selector)
    iframe.click(search_button_selector)

    # Wait for the results to load
    results_selector = "body > form > div.centrerad > table"
    iframe.wait_for_selector(results_selector)


def get_report_handles(iframe):
    """Get handles to the reports. 
    Clicking on these will load the popup with the report."""
    # All of the result rows has class forstaRad
    selector = ".forstaRad"
    iframe.wait_for_selector(selector)
    row_handles = iframe.query_selector_all(selector)
    assert row_handles is not None

    # The report is found in the last column
    report_handles = [row_handle.query_selector("td:last-child a")
                      for row_handle in row_handles
                      if row_handle]

    # Get rid of None values
    assert None not in report_handles
    report_handles = [rh 
                      for rh in report_handles 
                      if rh] # Just to make the type checker happy
    return report_handles


def extract_report_html_from_popup(popup) -> str:
    report_iframe_selector = "#lowerFrame > iframe"
    report_iframe_name = "DetaljFrame2"
    popup.wait_for_selector(report_iframe_selector)
    iframe = popup.frame(name=report_iframe_name)
    assert iframe is not None
    return iframe.content()


def get_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, features="lxml")
    text = soup.get_text(separator="\n", strip=True)
    return text


def scrape_report(report_link, page) -> str:
    """Click on report and srape the text."""
    with page.expect_popup() as popup_info:
        report_link.click()
    popup = popup_info.value
    report_html = extract_report_html_from_popup(popup)
    report_text = get_text_from_html(report_html)
    popup.close()
    return report_text


def main(max_reports: int, headless: bool, slow_mo: float):
    with playwright_browser(headless=headless, slow_mo=slow_mo) as browser:
        page = browser.new_page()
        page.goto("https://rattsinfosok.domstol.se/lagrummet/")

        # Wait for page to load
        page.wait_for_load_state("networkidle")

        # Get the frame
        iframe = get_frame(page)

        # Load the results (HDO is Högsta Domstolen)
        load_results(iframe, court_value="HDO", start_date="2020-01-01", end_date="2020-12-31")

        # Lets grab the links to reports
        report_handles = get_report_handles(iframe)

        # Before we save any files lets make sure the folder exists
        foldername = "reports"
        if not os.path.exists(foldername):
            os.makedirs(foldername)

        # For this demo i will just scrape the first 10 results
        for report_handle in report_handles[:max_reports]:
            report_text = scrape_report(report_handle, page)
            
            report_name = report_handle.text_content()
            assert report_name is not None
            filename = report_name.strip()

            with open(f"{foldername}/{filename}.txt", "w", encoding="utf8") as file:
                print(report_text, file=file)


if __name__ == "__main__":
    main(max_reports=10, headless=False, slow_mo=400)
