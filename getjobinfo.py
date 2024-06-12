import requests
from terminaltables import AsciiTable
from dotenv import load_dotenv
import os


def get_hh_vacancies(language, city_id):
    page = 1
    params = {
        "area": city_id,
        "text": language,
        "per_page": 100,
        "page": page,
    }
    headers = {"User-Agent": "api-test-agent"}
    base_url = 'https://api.hh.ru/vacancies/'
    all_vacancies = []

    while page < 50:
        page_params = params.copy()
        page_params['page'] = page
        response = requests.get(base_url, headers=headers, params=page_params)
        response.raise_for_status()
        json_response = response.json()
        vacancies = json_response.get('items', [])
        if not vacancies:
            break

        all_vacancies.extend(vacancies)
        total_pages = int(json_response.get('pages', 0))

        if page >= total_pages - 1:
            break

        page += 1
    return all_vacancies


def get_sj_vacancies(language):
    sj_id_key = os.environ["SJ_ID_KEY"]
    headers = {
        "X-Api-App-Id": sj_id_key,
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

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        vacancies = response.json()

        if not vacancies['objects']:
            break

        all_vacancies.extend(vacancies['objects'])
        page += 1

    return all_vacancies


def get_salary_hh(vacancie):
    salary = vacancie.get("salary")
    return salary


def get_predict_rub_salary_hh(salary):
    predict_rub_salary = None
    if salary:
        if salary["currency"] == "RUR":
            if not salary["from"] and salary["to"]:
                predict_rub_salary = None
            elif salary["from"]:
                if salary["to"]:
                    predict_rub_salary = (salary["from"] + salary["to"]) // 2
                else:
                    predict_rub_salary = salary["from"] * 1.2
            elif salary["to"]:
                predict_rub_salary = salary["to"] * 0.8
        else:
            predict_rub_salary = None
    else:
        predict_rub_salary = None
    return predict_rub_salary


def get_predict_rub_salary_sj(vacancie):
    payment_from = vacancie["payment_from"]
    payment_to = vacancie["payment_to"]
    currency = vacancie["currency"]
    predict_rub_salary = None
    if currency == "rub":
        if not payment_from and not payment_to:
            predict_rub_salary = None
        elif payment_from:
            if payment_to:
                predict_rub_salary = (payment_to + payment_from) // 2
            else:
                predict_rub_salary = payment_from * 1.2
        elif payment_to:
            predict_rub_salary = payment_to * 0.8
    else:
        predict_rub_salary = None
    return predict_rub_salary


def get_hh_vacancies_info(languages):
    languages_info = {}
    for language in languages:
        language_info = {}
        count_processed = 0
        salary_sum = 0
        vacancies = get_hh_vacancies(language, 1)
        count_language = len(vacancies)
        for vacancie in vacancies:
            salary = get_salary_hh(vacancie)
            predict_rub_salary = get_predict_rub_salary_hh(salary)
            if predict_rub_salary:
                count_processed = count_processed + 1
                salary_sum = salary_sum + predict_rub_salary
        language_info["vacancies_found"] = count_language
        language_info["vacancies_processed"] = count_processed
        language_info["average_salary"] = salary_sum // count_processed
        languages_info[language] = language_info
    return languages_info


def get_sj_vacancies_info(languages):
    languages_info = {}
    for language in languages:
        language_info = {}
        count_processed = 0
        salary_sum = 0
        sj_vacancies = get_sj_vacancies(language)
        count_language = len(sj_vacancies)
        for vacancie in sj_vacancies:
            predict_rub_salary = get_predict_rub_salary_sj(vacancie)
            if predict_rub_salary:
                count_processed = count_processed + 1
                salary_sum = salary_sum + predict_rub_salary
        if count_processed > 0:
            language_info["vacancies_found"] = count_language
            language_info["vacancies_processed"] = count_processed
            language_info["average_salary"] = salary_sum // count_processed
            languages_info[language] = language_info
    return languages_info


def make_vacancie_table(vacancies, site_name):
    headers = ["Язык программирования", "Вакансий найдено", "Вакансий обработано", "Средняя зарплата"]
    table = [
        headers
    ]
    for language, salary in vacancies.items():
        table.append([language, salary["vacancies_found"], salary["vacancies_processed"], salary["average_salary"]])
    table = AsciiTable(table, title=site_name)
    print(table.table)


if __name__ == "__main__":
    load_dotenv()
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
    vacancies = get_sj_vacancies_info(languages)
    make_vacancie_table(vacancies, "SuperJob")
    vacancies = get_hh_vacancies_info(languages)
    make_vacancie_table(vacancies, "HeadHunter")