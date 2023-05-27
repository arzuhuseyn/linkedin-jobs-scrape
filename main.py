import os
import time
from datetime import datetime
from collections import defaultdict

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By

from config import config

def safe_fail(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            return None

    return inner


class Xpath:
    ACCEPT_COOKIES = "/html/body/div/main/div[1]/div/section/div/div[2]/button[2]"
    USERNAME = '//*[@id="username"]'
    PASSWORD = '//*[@id="password"]'
    LOGIN_BUTTON = '//*[@id="organic-div"]/form/div[3]/button'
    JOBS_PAGE = '//*[@id="global-nav"]/div/nav/ul/li[3]/a'


class LinkedinJobSearchAgent:
    def __init__(
        self,
        username: str = config.LINKEDIN_USERNAME,
        password: str = config.LINKEDIN_PASSWORD,
        job_search: str = config.LINKEDIN_JOB_SEARCH,
        job_location: str = config.LINKEDIN_JOB_LOCATION,
    ):
        self.username = username
        self.password = password
        self.job_search = job_search
        self.job_location = job_location
        self._driver = webdriver.Chrome()
        self.state = defaultdict(list)
        self.time = datetime.now()

    @property
    def driver(self):
        return self._driver

    def maximize_window(self):
        self.driver.maximize_window()
        self.driver.switch_to.window(self.driver.current_window_handle)
        self.driver.implicitly_wait(10)

    def enter_to_the_site(self):
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(2)

    def accept_cookies(self):
        self.driver.find_element("xpath", Xpath.ACCEPT_COOKIES).click()

    def fill_user_credentials(self):
        self.driver.find_element("xpath", Xpath.USERNAME).send_keys(self.username)
        self.driver.find_element("xpath", Xpath.PASSWORD).send_keys(self.password)
        time.sleep(1)

    def click_login_button(self):
        self.driver.find_element("xpath", Xpath.LOGIN_BUTTON).click()
        self.driver.implicitly_wait(30)

    def click_jobs_page(self):
        self.driver.find_element("xpath", Xpath.JOBS_PAGE).click()
        time.sleep(3)

    def go_to_search_results_directly(self):
        self.driver.get(
            f"https://www.linkedin.com/jobs/search/?keywords={self.job_search}&location={self.job_location}"
        )
        time.sleep(1)

    @safe_fail
    def get_all_links_for_these_offers(self):
        print("Links are being collected now.")
        for page in range(2, 14):
            time.sleep(2)
            jobs_block = self.driver.find_element(
                By.CLASS_NAME, "jobs-search-results-list"
            )
            jobs_list = jobs_block.find_elements(
                By.CSS_SELECTOR, ".job-card-container--clickable"
            )

            for job in jobs_list:
                print(job)
                all_links = job.find_elements(By.TAG_NAME, "a")
                for a in all_links:
                    print(a)
                    if (
                        str(a.get_attribute("href")).startswith(
                            "https://www.linkedin.com/jobs/view"
                        )
                        and a.get_attribute("href") not in self.state["links"]
                    ):
                        self.state["links"].append(a.get_attribute("href"))
                    else:
                        pass
                # scroll down for each job element
                self.driver.execute_script("arguments[0].scrollIntoView();", job)

            print(f"Collecting the links in the page: {page-1}")
            # go to next page:
            self.driver.find_element(By.XPATH, f"//button[@aria-label='Page {page}']")
            time.sleep(3)
        print("Found " + str(len(self.state["links"])) + " links for job offers")
        return self.state["links"]

    def visit_each_link_one_by_one_to_scrape_the_information(self):
        # Visit each link one by one to scrape the information
        print("Visiting the links and collecting information just started.")
        for i in range(len(self.state["links"])):
            try:
                print(f"Visiting the link: {i}")
                self.driver.get(self.state["links"][i])
                i = i + 1
                time.sleep(2)
                # Click See more.
                self.driver.find_element(By.CLASS_NAME, "artdeco-card__actions").click()
                time.sleep(2)
            except:
                pass

        # Find the general information of the job offers
        contents = self.driver.find_elements(By.CLASS_NAME, "p5")
        company_name = self.driver.find_element(
            By.CLASS_NAME, "jobs-unified-top-card__company-name"
        ).text
        job_title = self.driver.find_element(By.TAG_NAME, "h1").text
        for content in contents:
            print(f"Scraping the Job Offer {content}")
            try:
                self.state["job_titles"].append(
                    content.find_element(By.TAG_NAME, "h1").text
                )
                self.state["company_names"].append(
                    content.find_element(
                        By.CLASS_NAME, "jobs-unified-top-card__company-name"
                    ).text
                )
                self.state["company_locations"].append(
                    content.find_element(
                        By.CLASS_NAME, "jobs-unified-top-card__bullet"
                    ).text
                )
                self.state["work_methods"].append(
                    content.find_element(
                        By.CLASS_NAME, "jobs-unified-top-card__workplace-type"
                    ).text
                )
                self.state["post_dates"].append(
                    content.find_element(
                        By.CLASS_NAME, "jobs-unified-top-card__posted-date"
                    ).text
                )
                self.state["work_times"].append(
                    content.find_element(
                        By.CLASS_NAME, "jobs-unified-top-card__job-insight"
                    ).text
                )
                print(f"Scraping the Job Offer {j} DONE.")
                j += 1

            except:
                pass
            time.sleep(2)

            # Scraping the job description
        job_description = self.driver.find_elements(
            By.CLASS_NAME, "jobs-description__content"
        )
        for description in job_description:
            job_text = description.find_element(
                By.CLASS_NAME, "jobs-box__html-content"
            ).text
            job_text = f"Company Name: {company_name} \n Job Title: {job_title} \n"
            job_text = (
                job_text + f"\n LinkedIn Job Offer Link: {self.state['links'][i]}"
            )
            self.state["job_desc"].append(job_text)
            print(f"Scraping the Job Offer {j}")
            time.sleep(2)

    def create_csv(self):
        # Creating the dataframe
        df = pd.DataFrame(
            list(
                zip(
                    self.state["job_titles"],
                    self.state["company_names"],
                    self.state["company_locations"],
                    self.state["work_methods"],
                    self.state["post_dates"],
                    self.state["work_times"],
                )
            ),
            columns=[
                "job_title",
                "company_name",
                "company_location",
                "work_method",
                "post_date",
                "work_time",
            ],
        )
        self.state["time"] = f"{self.time.hour}:{self.time.minute}"
        df.to_csv(f"scrape_results/job_offers_{self.state['time']}.csv", index=False)
        return df

    def output_job_descriptions_to_txt_file(self):
        # Output job descriptions to txt file
        with open(
            f"scrape_results/job_descriptions_{self.state['time']}.txt",
            "w",
            encoding="utf-8",
        ) as f:
            for line in self.state["job_desc"]:
                line = line + "{pagebreak}"
                f.write(line)
                f.write("\n")

    def close_the_driver(self):
        self.driver.quit()

    def run(self):
        self.maximize_window()
        self.enter_to_the_site()
        self.accept_cookies()
        self.fill_user_credentials()
        self.click_login_button()
        self.click_jobs_page()
        self.go_to_search_results_directly()
        self.get_all_links_for_these_offers()
        self.visit_each_link_one_by_one_to_scrape_the_information()
        self.create_csv()
        self.output_job_descriptions_to_txt_file()
        self.close_the_driver()


if __name__ == "__main__":
    if not os.path.exists("scrape_results"):
        os.makedirs("scrape_results")
    LinkedinJobSearchAgent().run()