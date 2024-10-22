import argparse
import datetime
import json
import sqlalchemy

import models


def load_json(file):
    with open(file) as fp:
        data = json.load(fp)
    return data


class SQL:
    @staticmethod
    def add_documents(documents, session):
        for doc in documents:
            first_published = (datetime.datetime.strptime(doc.get('first_published'), '%Y-%m-%d') if doc.get(
                'first_published') else None)
            last_updated = datetime.datetime.strptime(doc.get('last_updated'), '%Y-%m-%d')
            publication_date = datetime.datetime.strptime(doc.get('publication_date'), '%Y-%m-%d')

            document = models.Document(
                id=doc["id"],
                label=doc.get('label'),
                description=doc.get('description'),
                alternative_labels=doc.get('alternativeLabels'),
                citation=doc.get('citation'),
                document_type=doc.get('document_type'),
                drug_name_brand=doc.get('drug_name_brand'),
                drug_name_generic=doc.get('drug_name_generic'),
                first_published=first_published,
                last_updated=last_updated,
                organization=doc.get('organization'),
                publication_date=publication_date,
                url=doc.get('url'),
                url_epar=doc.get('url_epar')
            )
            session.add(document)
        return session


def main():
    session = models.Session()

    root = "/Users/brendan/GitHub/projects/euro-moalmanac-db/data/referenced"
    documents = load_json(f"{root}/documents.json")
    for doc in documents:
        first_published = datetime.datetime.strptime(doc.get('first_published'), '%Y-%m-%d') if doc.get('first_published') else None
        last_updated = datetime.datetime.strptime(doc.get('last_updated'), '%Y-%m-%d')
        publication_date = datetime.datetime.strptime(doc.get('publication_date'), '%Y-%m-%d')

        document = models.Document(
            id=doc["id"],
            label=doc.get('label'),
            description=doc.get('description'),
            alternative_labels=doc.get('alternativeLabels'),
            citation=doc.get('citation'),
            document_type=doc.get('document_type'),
            drug_name_brand=doc.get('drug_name_brand'),
            drug_name_generic=doc.get('drug_name_generic'),
            first_published=first_published,
            last_updated=last_updated,
            organization=doc.get('organization'),
            publication_date=publication_date,
            url=doc.get('url'),
            url_epar=doc.get('url_epar')
        )
        session.add(document)

    indications = load_json(f"{root}/indications.json")
    for ind in indications:
        reimbursement_date = datetime.datetime.strptime(ind.get('reimbursement_date'), '%Y-%m-%d') if ind.get('reimbursement_date') else None

        indication = models.Indication(
            id=ind['id'],
            document_id=ind.get('document_id'),
            indication=ind.get('indication'),
            icd10=ind.get('icd10'),
            regimen_code=ind.get('regimen_code'),
            reimbursement_category=ind.get('reimbursement_category'),
            reimbursement_date=reimbursement_date,
            reimbursement_details=ind.get('reimbursement_details')
        )
        session.add(indication)

    session.commit()
    session.close()

    return ''


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        prog='Create MOAlmanac SQLite3 file from referenced JSONs',
        description='Using referenced JSON files, create SQLite3 db'
    )
    args = arg_parser.parse_args()

    main()
