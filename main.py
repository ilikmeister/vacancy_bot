import asyncio
from telegram import Bot
from telegram.ext import Application
import os
import time
from bs4 import BeautifulSoup
import requests

# Set up headers for the requests
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
BASE_URL = "https://www.agropraktika.eu/vacancies?page="

# Initialize the bot with the token
bot = Application.builder().token(BOT_TOKEN).build()

async def get_total_pages():
    print("Fetching total pages...")
    response = requests.get(url=BASE_URL + "1", headers=headers)
    if response.status_code == 200:
        print("Page fetched successfully.")
    else:
        print(f"Failed to fetch page: {response.status_code}")
        return 1

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the pagination links to get the last page
    pagination_links = soup.select("a[aria-label^='Go to page']")
    if pagination_links:
        # Extract unique page numbers
        page_numbers = {int(link.text.strip()) for link in pagination_links if link.text.strip().isdigit()}

        # Get the highest page number
        if page_numbers:
            last_page_number = max(page_numbers)
            print(f"Total pages found: {last_page_number}")
            return last_page_number
        else:
            print("No valid page numbers found in pagination links.")
            return 1
    else:
        print("No pagination links found, defaulting to 1 page.")
        return 1  # Default to 1 page if no pagination is found

async def check_vacancies_on_page(page_number):
    print(f"Checking vacancies on page {page_number}...")
    response = requests.get(url=BASE_URL + str(page_number), headers=headers)
    if response.status_code == 200:
        print(f"Page {page_number} fetched successfully.")
    else:
        print(f"Failed to fetch page {page_number}: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all vacancy items on the page
    vacancy_items = soup.find_all('li', class_='vacancy-item')

    available_jobs = []
    for vacancy in vacancy_items:
        alert_div = vacancy.find('div', id='alert-additional-content-1')
        if alert_div is not None:
            title = vacancy.find('h4').text.strip()
            link = vacancy.find('a', class_='cover')['href']
            available_jobs.append(f"- {title}\n{link}")
    
    if available_jobs:
        print(f"Found {len(available_jobs)} available jobs on page {page_number}.")
    else:
        print(f"No available jobs on page {page_number}.")
    
    return available_jobs

async def check_all_vacancies():
    print("Checking all vacancies...")
    total_pages = await get_total_pages()  # Await the total pages function
    all_available_jobs = []

    for page_number in range(1, total_pages + 1):
        available_jobs = await check_vacancies_on_page(page_number)  # Await each page check
        all_available_jobs.extend(available_jobs)

    if all_available_jobs:
        message = "Қолжетімді акансиялар:\n\n" + "\n\n".join(all_available_jobs)
        print(f"Sending message with {len(all_available_jobs)} jobs.")
        await bot.send_message(chat_id=CHAT_ID, text=message)  # Await the send_message call
    else:
        print("No new jobs found, nothing to send.")

async def main():
    total_cpu_time = 0
    while True:
        start_time = time.process_time()

        await check_all_vacancies()  # Await the function that checks all vacancies
        
        end_time = time.process_time()
        iteration_cpu_time = end_time - start_time
        total_cpu_time += iteration_cpu_time
        print(f"Iteration CPU time: {iteration_cpu_time:.4f} seconds")
        print(f"Total CPU time used: {total_cpu_time:.2f} seconds")
                
        await asyncio.sleep(30)  # Use async sleep to avoid blocking the event loop

if __name__ == "__main__":
    print("Starting the script...")
    asyncio.run(main())  # Run the asynchronous main function

