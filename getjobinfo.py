import requests
from terminaltables import AsciiTable
from dotenv import load_dotenv
import os
import pprint


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
        total_pages = int(hh_result.get('pages', 0))

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
    expected_rub_salary = None
    if currency == "rub" or currency == "RUR":
        if payment_from and payment_to:
            expected_rub_salary = (payment_to + payment_from) // 2
        elif payment_from:
            expected_rub_salary = payment_from * 1.2
        elif payment_to:
            expected_rub_salary = payment_to * 0.8
    return expected_rub_salary


def process_vacancies(vacancies, site):
    count_processed = 0
    salary_sum = 0
    language_vacancy = {}
    all_vacancies, count_language = vacancies
    for vacancy in all_vacancies:
        if site == "SuperJob":
            payment_from = vacancy["payment_from"]
            payment_to = vacancy["payment_to"]
            currency = vacancy["currency"]
            expected_rub_salary = get_rub_salary(payment_from, payment_to, currency)
        else:
            salary = vacancy.get("salary")
            if salary:
                payment_from = salary["from"]
                payment_to = salary["to"]
                currency = salary["currency"]
            else:
                payment_from = None
                payment_to = None
                currency = None
            expected_rub_salary = get_rub_salary(payment_from, payment_to, currency)
        if expected_rub_salary:
            count_processed = count_processed + 1
            salary_sum = salary_sum + expected_rub_salary
    language_vacancy["vacancies_found"] = count_language
    language_vacancy["vacancies_processed"] = count_processed
    language_vacancy["average_salary"] = None
    if count_processed:
        language_vacancy["average_salary"] = salary_sum // count_processed
    return language_vacancy


def get_language_vacancies(site, languages, sj_id):
    language_vacancies = {}
    for language in languages:
        if site == "SuperJob":
            vacancies = get_sj_vacancies(language, sj_id)
        else:
            vacancies = get_hh_vacancies(language, 1)
        language_vacancy = process_vacancies(vacancies, site)
        if language_vacancy:
            language_vacancies[language] = language_vacancy
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
    sj_id = os.environ["SJ_ID_KEY"]
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
    sites = [
        'SuperJob',
        'HeadHunter'
    ]
    for site in sites:
        vacancies = get_language_vacancies(site, languages, sj_id)
        print(make_vacancy_table(vacancies, site))