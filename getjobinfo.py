import requests
from terminaltables import AsciiTable
from dotenv import load_dotenv
import os
import argparse


def get_hh_vacancies(language, city_id):
    page = 1
    total_found = 0
    params = {
        "area": city_id,
        "text": language,
        "per_page": 100,
        "page": page,
    }
    headers = {"User-Agent": "api-test-agent"}
    base_url = 'https://api.hh.ru/vacancies/'
    all_vacancies = []

    while True:
        page_params = params.copy()
        page_params['page'] = page
        response = requests.get(base_url, headers=headers, params=page_params)
        response.raise_for_status()
        hh_result = response.json()
        vacancies = hh_result.get('items', [])
        total_found = hh_result.get("found", 0)
        if not vacancies:
            break
        all_vacancies.extend(vacancies)
        total_pages = hh_result.get('pages', 0)
        if page >= total_pages - 1:
            break
        page += 1
    return all_vacancies, total_found


def get_sj_vacancies(language, sj_id):
    headers = {
        "X-Api-App-Id": sj_id,
    }
    url = "https://api.superjob.ru/2.0/vacancies/"
    page = 0
    all_vacancies = []

    while True:
        params = {
            "town": "Moscow",
            "page": page,
            "keyword": language
        }

        sj_result = requests.get(url, headers=headers, params=params)
        sj_result.raise_for_status()
        vacancies = sj_result.json()
        total_found = vacancies.get('total', 0)
        if not vacancies['objects']:
            break

        all_vacancies.extend(vacancies['objects'])
        page += 1

    return all_vacancies, total_found


def get_rub_salary(payment_from, payment_to, currency):
    if currency not in ["rub", "RUR"]:
        return None
    if payment_from and payment_to:
        return (payment_to + payment_from) // 2
    if payment_from:
        return payment_from * 1.2
    if payment_to:
        return payment_to * 0.8
    return None


def process_vacancies_sj(all_vacancies, total_vacancies):
    processed_count = 0
    salary_sum = 0
    for vacancy in all_vacancies:
        payment_from = vacancy["payment_from"]
        payment_to = vacancy["payment_to"]
        currency = vacancy["currency"]
        expected_rub_salary = get_rub_salary(payment_from, payment_to, currency)
        if expected_rub_salary:
            processed_count += 1
            salary_sum += expected_rub_salary
    return {
        "vacancies_found": total_vacancies,
        "vacancies_processed": processed_count,
        "average_salary": salary_sum // processed_count if processed_count else None
    }


def process_vacancies_hh(all_vacancies, total_vacancies):
    payment_from = None
    payment_to = None
    currency = None
    processed_count = 0
    salary_sum = 0
    for vacancy in all_vacancies:
        salary = vacancy.get("salary")
        if salary:
            payment_from = salary["from"]
            payment_to = salary["to"]
            currency = salary["currency"]
        expected_rub_salary = get_rub_salary(payment_from, payment_to, currency)
        if expected_rub_salary:
            processed_count += 1
            salary_sum += expected_rub_salary
    return {
        "vacancies_found": total_vacancies,
        "vacancies_processed": processed_count,
        "average_salary": salary_sum // processed_count if processed_count else None
    }


def get_language_vacancies_hh(languages, identifier):
    language_vacancies = {}
    for language in languages:
        all_vacancies, total_vacancies = get_hh_vacancies(language, identifier)
        language_vacancies[language] = process_vacancies_hh(all_vacancies, total_vacancies)
    return language_vacancies


def get_language_vacancies_sj(languages, identifier):
    language_vacancies = {}
    for language in languages:
        all_vacancies, total_vacancies = get_sj_vacancies(language, identifier)
        language_vacancies[language] = process_vacancies_sj(all_vacancies, total_vacancies)
    return language_vacancies


def make_vacancy_table(vacancies, site_name):
    headers = ["Язык программирования", "Вакансий найдено", "Вакансий обработано", "Средняя зарплата"]
    table = [
        headers
    ]
    for language, salary in vacancies.items():
        table.append([language, salary["vacancies_found"], salary["vacancies_processed"], salary["average_salary"]])
    table = AsciiTable(table, title=site_name).table
    return table


if __name__ == "__main__":
    load_dotenv()
    api_key = os.environ["SJ_ID_KEY"]
    languages = [
        'JavaScript',
        'Java',
        'Python',
        'Ruby',
        'PHP',
        'C++',
        'CSS',
        'C#',
    ]
    parser = argparse.ArgumentParser(description='Process some id from sites.')
    parser.add_argument('city_id', help='city id to search on the Headhunter')
    args = parser.parse_args()
    vacancies = get_language_vacancies_sj(languages, api_key)
    print(make_vacancy_table(vacancies, "SuperJob"))
    vacancies = get_language_vacancies_hh(languages, args.city_id)
    print(make_vacancy_table(vacancies, "HeadHunter"))

