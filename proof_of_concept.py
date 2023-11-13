from contextlib import contextmanager
from time import sleep

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


def load_results(iframe, start_date: str, end_date: str) -> None:
    """Load the results in the iframe.
    start_date and end_date must be in the format yyyy-mm-dd."""
    
    # Select all courts
    dropdown_value = "ALLAMYND"
    dropdown_selector = "#select-domstolmyndighet"
    iframe.wait_for_selector(dropdown_selector)
    iframe.select_option(dropdown_selector, dropdown_value)
    
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


def click_on_first_result(iframe) -> None:
    """Clicks on the first result."""
    # All of the result rows are either the class "forstaRad" or "andraRad"
    class1 = "forstaRad"
    class2 = "andraRad"
    xpath_expression = f"//tr[contains(@class, '{class1}') or contains(@class, '{class2}')]"
    
    # Get the row
    row_handle = iframe.wait_for_selector(f"xpath={xpath_expression}")
    assert row_handle is not None
    
    # The report is found in the last column
    link_handle = row_handle.query_selector("td:last-child a")
    assert link_handle is not None
    link_handle.click()


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


def main(filename: str, headless: bool, slow_mo: float):
    with playwright_browser(headless=headless, slow_mo=slow_mo) as browser:
        page = browser.new_page()
        page.goto("https://rattsinfosok.domstol.se/lagrummet/")

        # Wait for page to load
        page.wait_for_load_state("networkidle")

        # Get the frame
        iframe = get_frame(page)

        # Load the results
        load_results(iframe, start_date="2020-01-01", end_date="2021-01-01")

        # We can now get the html of the results page and scrape information
        results_html = iframe.content()
        
        # For this demo i will just scrape the first result
        with page.expect_popup() as popup_info:
            click_on_first_result(iframe)
        popup = popup_info.value

        report_html = extract_report_html_from_popup(popup)
        report_text = get_text_from_html(report_html)
        
        with open(filename, "w", encoding="utf8") as file:
            print(report_text, file=file)
            
        sleep(slow_mo / 1000) # Allows us to see the popup
        popup.close() # Make sure to close each popup before moving on to the next to save memory
        sleep(slow_mo / 1000)


if __name__ == "__main__":
    main(filename="report.txt", headless=False, slow_mo=400)
