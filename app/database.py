import argparse
import datetime
import json

from . import models


class Process:
    @staticmethod
    def load_json(file):
        with open(file) as fp:
            data = json.load(fp)
        return data

    @staticmethod
    def parse_date(date_string, date_string_format='%Y-%m-%d'):
        try:
           date_object = datetime.datetime.strptime(date_string, date_string_format)
           return date_object.date()
        except ValueError:
            return None


class SQL:
    @staticmethod
    def add_about(record, session):
        last_updated = Process.parse_date(record['last_updated'])
        about = models.About(
            id=0,
            github=record.get('github'),
            label=record.get('label'),
            license=record.get('license'),
            release=record.get('release'),
            url=record.get('url'),
            last_updated=last_updated,
        )
        session.add(about)

    @staticmethod
    def add_documents(documents, session):
        for doc in documents:
            first_published = Process.parse_date(doc.get('first_published')) if doc.get('first_published') else None
            last_updated = Process.parse_date(doc.get('last_updated'))
            publication_date = Process.parse_date(doc.get('publication_date'))

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

    @staticmethod
    def add_biomarkers(records, session):
        for record in records:
            biomarker = models.Biomarker(
                id=record['id'],
                biomarker_type=record['biomarker_type'],
                display=record.get('_display'),
                present=record.get('_present'),
                marker=record.get('marker'),
                unit=record.get('unit'),
                equality=record.get('equality'),
                value=record.get('value'),
                gene=record.get('gene'),
                chromosome=record.get('chromosome'),
                start_position=record.get('start_position'),
                end_position=record.get('end_position'),
                reference_allele=record.get('reference_allele'),
                alternate_allele=record.get('alterante_allele'),
                cdna_change=record.get('cdna_change'),
                protein_change=record.get('protein_change'),
                variant_annotation=record.get('variant_annotation'),
                exon=record.get('exon'),
                rsid=record.get('rsid'),
                hgvsg=record.get('hgvsg'),
                hgvsc=record.get('hgvsc'),
                requires_oncogenic=record.get('requires_oncogenic'),
                requires_pathogenic=record.get('requires_pathogenic'),
                gene1=record.get('gene1'),
                gene2=record.get('gene2'),
                rearrangement_type=record.get('rearrangement_type'),
                locus=record.get('locus'),
                direction=record.get('direction'),
                cytoband=record.get('cytoband'),
                arm=record.get('arm'),
                status=record.get('status')
            )
            session.add(biomarker)

    @staticmethod
    def add_contexts(records, session):
        for record in records:
            context = models.Context(
                id=record["id"],
                disease=record.get('disease'),
                display=record.get('display'),
                oncotree_code=record.get('oncotree_code'),
                oncotree_term=record.get('oncotree_term'),
                solid_tumor=record.get('solid_tumor')
            )
            session.add(context)

    @staticmethod
    def add_implications(records, session):
        for record in records:
            implication = models.Implication(
                id=record['id'],
                implication_type=record.get('implication_type'),
                _therapy=record.get('_therapy')
            )
            session.add(implication)

            for therapy_id in record['therapy']:
                therapy = session.query(models.Therapy).filter_by(id=therapy_id).first()
                if therapy:
                    implication.therapy.append(therapy)
                else:
                    print(f"therapy {therapy_id} not found for {record}")

    @staticmethod
    def add_indications(records, session):
        for record in records:
            reimbursement_date = datetime.datetime.strptime(record.get('reimbursement_date'), '%Y-%m-%d') if record.get(
                'reimbursement_date') else None

            indication = models.Indication(
                id=record['id'],
                document_id=record.get('document_id'),
                indication=record.get('indication'),
                icd10=record.get('icd10'),
                regimen_code=record.get('regimen_code'),
                reimbursement_category=record.get('reimbursement_category'),
                reimbursement_date=reimbursement_date,
                reimbursement_details=record.get('reimbursement_details')
            )
            session.add(indication)

    @staticmethod
    def add_organizations(records, session):
        for record in records:
            last_updated = Process.parse_date(record.get('last_updated'))

            organization = models.Organization(
                id=record["id"],
                label=record.get('label'),
                description=record.get('description'),
                last_updated=last_updated
            )
            session.add(organization)

    @staticmethod
    def add_statements(records, session):
        for record in records:
            last_updated = Process.parse_date(record.get('last_updated'))

            statement = models.Statement(
                id=record['id'],
                document_id=record.get('document_id'),
                context_id=record.get('context_id'),
                description=record.get('description'),
                evidence=record.get('evidence'),
                implication_id=record.get('implication_id'),
                indication_id=record.get('indication_id'),
                last_updated=last_updated,
                deprecated=record.get('deprecated'),
            )
            session.add(statement)

            for biomarker_id in record['biomarkers']:
                biomarker = session.query(models.Biomarker).filter_by(id=biomarker_id).first()
                if biomarker:
                    statement.biomarkers.append(biomarker)
                else:
                    print(f"biomarker {biomarker_id} not found for {record}")

    @staticmethod
    def add_therapies(records, session):
        for record in records:
            therapy = models.Therapy(
                id=record['id'],
                therapy_name=record.get('therapy_name'),
                therapy_strategy=record.get('therapy_strategy'),
                therapy_type=record.get('therapy_type')
            )
            session.add(therapy)


def main(referenced_dictionary):
    with models.Session() as session:
        root = f"{referenced_dictionary}"

        about = Process.load_json(f"{root}/about.json")
        SQL.add_about(record=about, session=session)
        session.commit()

        organizations = Process.load_json(f"{root}/organizations.json")
        SQL.add_organizations(records=organizations, session=session)
        session.commit()

        biomarkers = Process.load_json(f"{root}/biomarkers.json")
        SQL.add_biomarkers(records=biomarkers, session=session)
        session.commit()

        contexts = Process.load_json(f"{root}/context.json")
        SQL.add_contexts(records=contexts, session=session)
        session.commit()

        documents = Process.load_json(f"{root}/documents.json")
        SQL.add_documents(documents=documents, session=session)
        session.commit()

        indications = Process.load_json(f"{root}/indications.json")
        SQL.add_indications(records=indications, session=session)
        session.commit()

        therapies = Process.load_json(f"{root}/therapies.json")
        SQL.add_therapies(records=therapies, session=session)
        session.commit()

        implications = Process.load_json(f"{root}/implications.json")
        SQL.add_implications(records=implications, session=session)
        session.commit()

        statements = Process.load_json(f"{root}/statements.json")
        SQL.add_statements(records=statements, session=session)
        session.commit()

        session.close()

    return 'Success!'


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        prog='Create MOAlmanac SQLite3 file from referenced JSONs',
        description='Using referenced JSON files, create SQLite3 db'
    )
    arg_parser.add_argument(
        '--input',
        '-i',
        default='data/referenced',
        help='Directory for referenced moalmanac db json files'
    )
    args = arg_parser.parse_args()

    main(
        referenced_dictionary=args.input
    )
