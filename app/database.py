import argparse
import datetime
import json

import models


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
        about = models.About(
            id=0,
            github=record.get('github'),
            name=record.get('name'),
            license=record.get('license'),
            release=record.get('release'),
            url=record.get('url'),
            last_updated=Process.parse_date(record.get('last_updated'))
        )
        session.add(about)

    @staticmethod
    def add_agents(records, session):
        for record in records:
            agent = models.Agents(
                id=record.get('id'),
                type=record.get('type'),
                subtype=record.get('subtype'),
                name=record.get('name'),
                description=record.get('description')
            )
            session.add(agent)

    @staticmethod
    def add_biomarkers(records, session):
        for record in records:
            moalmanac_representation = {}
            for item in record.get('extensions'):
                moalmanac_representation[item.get('name')] = item.get('value')

            gene_ids = record.get('genes', [])
            if gene_ids:
                gene_instances = session.query(models.Genes).filter(models.Genes.id.in_(gene_ids)).all()
            else:
                gene_instances = []

            biomarker = models.Biomarkers(
                id=record.get('id'),
                name=record.get('name'),
                genes=gene_instances,
                biomarker_type=moalmanac_representation.get('biomarker_type', None),
                present=moalmanac_representation.get('_present', None),
                marker=moalmanac_representation.get('marker', None),
                unit=moalmanac_representation.get('unit', None),
                equality=moalmanac_representation.get('equality', None),
                value=moalmanac_representation.get('value', None),
                chromosome=moalmanac_representation.get('chromosome', None),
                start_position=moalmanac_representation.get('start_position', None),
                end_position=moalmanac_representation.get('end_position', None),
                reference_allele=moalmanac_representation.get('reference_allele', None),
                alternate_allele=moalmanac_representation.get('alternate_allele', None),
                cdna_change=moalmanac_representation.get('cdna_change', None),
                protein_change=moalmanac_representation.get('protein_change', None),
                variant_annotation=moalmanac_representation.get('variant_annotation', None),
                exon=moalmanac_representation.get('exon', None),
                rsid=moalmanac_representation.get('rsid', None),
                hgvsg=moalmanac_representation.get('hgvsg', None),
                hgvsc=moalmanac_representation.get('hgvsc', None),
                requires_oncogenic=moalmanac_representation.get('requires_oncogenic', None),
                requires_pathogenic=moalmanac_representation.get('requires_pathogenic', None),
                rearrangement_type=moalmanac_representation.get('rearrangement_type', None),
                locus=moalmanac_representation.get('locus', None),
                direction=moalmanac_representation.get('direction', None),
                cytoband=moalmanac_representation.get('cytoband', None),
                arm=moalmanac_representation.get('arm', None),
                status=moalmanac_representation.get('status', None)
            )
            session.add(biomarker)

    @staticmethod
    def add_codings(records, session):
        for record in records:
            coding = models.Codings(
                id=record.get('id'),
                code=record.get('code'),
                name=record.get('name'),
                system=record.get('system'),
                systemVersion=record.get('systemVersion'),
                iris=record.get('iris')[0] # This will be a list, eventually
            )
            session.add(coding)

    @staticmethod
    def add_contributions(records, session):
        for record in records:
            contribution = models.Contributions(
                id=record.get('id'),
                type=record.get('type'),
                agent_id=record.get('agent_id'),
                description=record.get('description'),
                date=Process.parse_date(record.get('last_updated'))
            )
            session.add(contribution)

    @staticmethod
    def add_diseases(records, session):
        for record in records:
            mapping_ids = record.get('mappings', [])
            if mapping_ids:
                mapping_instances = session.query(models.Mappings).filter(models.Mappings.id.in_(mapping_ids)).all()
            else:
                mapping_instances = []
            extensions = record.get('extensions', [])

            disease = models.Diseases(
                id=record.get('id'),
                concept_type=record.get('conceptType'),
                name=record.get('name'),
                primary_coding_id=record.get('primary_coding_id'),
                mappings=mapping_instances,
                solid_tumor=extensions[0].get('value') if extensions else None
            )
            session.add(disease)

    @staticmethod
    def add_documents(records, session):
        for record in records:
            document = models.Documents(
                id=record.get('id'),
                type=record.get('type'),
                subtype=record.get('subtype'),
                name=record.get('name'),
                aliases=record.get('aliases', None),
                citations=record.get('citation', None),
                company=record.get('company', None),
                drug_name_brand=record.get('drug_name_brand', None),
                drug_name_generic=record.get('drug_name_generic', None),
                first_published=Process.parse_date(record.get('first_published', None)),
                access_date=Process.parse_date(record.get('access_date', None)),
                organization_id=record.get('organization_id', None),
                publication_date=Process.parse_date(record.get('publication_date', None)),
                url=record.get('url', None),
                url_drug=record.get('url_drug', None),
                application_number=record.get('application_number', None)
            )
            session.add(document)

    @staticmethod
    def add_genes(records, session):
        for record in records:
            mapping_ids = record.get('mappings', [])
            if mapping_ids:
                mapping_instances = session.query(models.Mappings).filter(models.Mappings.id.in_(mapping_ids)).all()
            else:
                mapping_instances = []
            extensions = record.get('extensions', [])

            gene = models.Genes(
                id=record.get('id'),
                concept_type=record.get('conceptType'),
                name=record.get('name'),
                primary_coding_id=record.get('primary_coding_id'),
                mappings=mapping_instances,
                location=extensions[0].get('value') if extensions else None,
                location_sortable=extensions[1].get('value') if extensions else None
            )
            session.add(gene)

    @staticmethod
    def add_indications(records, session):
        for record in records:
            indication = models.Indication(
                id=record.get('id'),
                document_id=record.get('document_id'),
                indication=record.get('indication'),
                icd10=record.get('icd10'),
                regimen_code=record.get('regimen_code'),
                reimbursement_category=record.get('reimbursement_category'),
                reimbursement_date=Process.parse_date(record.get('reimbursement_date', None)),
                reimbursement_details=record.get('reimbursement_details'),
                description=record.get('description', None),
                initial_approval_date=Process.parse_date(record.get('initial_approval_date', None)),
                initial_approval_url=record.get('initial_approval_url', None),
                raw_biomarkers=record.get('raw_biomarkers', None),
                raw_therapeutics=record.get('raw_therapeutics', None),
                raw_cancer_type=record.get('raw_cancer_type', None),
                date_regular_approval=Process.parse_date(record.get('date_regular_approval', None)),
                date_accelerated_approval=Process.parse_date(record.get('date_accelerated_approval', None))
            )
            session.add(indication)

    @staticmethod
    def add_mappings(records, session):
        for record in records:
            mapping = models.Mappings(
                id=record.get('id'),
                primary_coding_id=record.get('primary_coding_id'),
                coding_id=record.get('coding_id'),
                relation=record.get('relation')
            )
            session.add(mapping)

    @staticmethod
    def add_organizations(records, session):
        for record in records:
            organization = models.Organization(
                id=record['id'],
                name=record.get('name'),
                description=record.get('description'),
                url=record.get('url'),
                last_updated=Process.parse_date(record.get('last_updated'))
            )
            session.add(organization)

    @staticmethod
    def add_propositions(records, session):
        for record in records:
            proposition = models.Propositions(
                id=record.get('id'),
                type=record.get('type'),
                predicate=record.get('predicate'),
                biomarkers=record.get('biomarkers'),
                condition_qualifier_id=record.get('condition_qualifier_id'),
                therapy_id=record.get('therapy_id'),
                therapy_group_id=record.get('therapy_group_id')
            )
            session.add(proposition)

    @staticmethod
    def add_statements(records, session):
        for record in records:
            statement = models.Statements(
                id=record['id'],
                type=record.get('type'),
                description=record.get('description'),
                contributions=record.get('contributions'),
                documents=record.get('documents'),
                proposition_id=record.get('proposition_id'),
                direction=record.get('direction'),
                strength_id=record.get('strength_id'),
                indication_id=record.get('indication_id')
            )
            session.add(statement)

    @staticmethod
    def add_strengths(records, session):
        for record in records:
            strength = models.Strengths(
                id=record.get('id'),
                concept_type=record.get('conceptType'),
                name=record.get('name'),
                primary_coding_id=record.get('primary_coding_id'),
                mappings=record.get('mappings')
            )
            session.add(strength)

    @staticmethod
    def add_therapies(records, session):
        for record in records:
            mapping_ids = record.get('mappings', [])
            mapping_instances = []
            if mapping_ids:
                mapping_instances = (
                    session
                    .query(models.Mappings)
                    .filter(models.Mappings.id.in_(mapping_ids))
                    .all()
                )
            extensions = record.get('extensions', [])
            if extensions:
                strategy_ids = extensions[0].get('value')
                strategy_instances = []
                #strategy_instances = (
                #    session
                #    .query(models.TherapyStrategies)
                #    .filter(models.TherapyStrategies.id.in_(strategy_ids))
                #    .all()
                #)
                therapy_type = extensions[1].get('value', None)
            else:
                strategy_instances = []
                therapy_type = None

            therapy = models.Therapies(
                id=record.get('id'),
                concept_type=record.get('conceptType'),
                name=record.get('name'),
                primary_coding_id=record.get('primary_coding_id'),
                mappings=mapping_instances,
                therapy_strategy=[],
                therapy_strategy_description=record.get('therapy_strategy_description'),
                therapy_type=therapy_type,
                therapy_type_description=record.get('therapy_type_description')
            )
            session.add(therapy)

    @staticmethod
    def add_therapy_groups(records, session):
        for record in records:
            therapy_ids = record.get('therapies', [])
            therapy_instances = []
            if therapy_ids:
                therapy_instances = (
                    session
                    .query(models.Mappings)
                    .filter(models.Mappings.id.in_(therapy_ids))
                    .all()
                )

            print(record.get('id'), therapy_instances)
            therapy_group = models.TherapyGroups(
                id=record.get('id'),
                membership_operator=record.get('membership_operator'),
                therapies=therapy_instances
            )
            session.add(therapy_group)


def main(referenced_dictionary):
    with models.Session() as session:
        root = f"{referenced_dictionary}"

        about = Process.load_json(f"{root}/about.json")
        SQL.add_about(record=about, session=session)
        session.commit()

        codings = Process.load_json(f"{root}/codings.json")
        SQL.add_codings(records=codings, session=session)
        session.commit()

        mappings = Process.load_json(f"{root}/mappings.json")
        SQL.add_mappings(records=mappings, session=session)
        session.commit()

        agents = Process.load_json(f"{root}/agents.json")
        SQL.add_agents(records=agents, session=session)
        session.commit()

        genes = Process.load_json(f"{root}/genes.json")
        SQL.add_genes(records=genes, session=session)
        session.commit()

        biomarkers = Process.load_json(f"{root}/biomarkers.json")
        SQL.add_biomarkers(records=biomarkers, session=session)
        session.commit()

        diseases = Process.load_json(f"{root}/diseases.json")
        SQL.add_diseases(records=diseases, session=session)
        session.commit()

        therapies = Process.load_json(f"{root}/therapies.json")
        SQL.add_therapies(records=therapies, session=session)
        session.commit()

        therapy_groups = Process.load_json(f"{root}/therapy_groups.json")
        SQL.add_therapy_groups(records=therapy_groups, session=session)
        session.commit()

        contributions = Process.load_json(f"{root}/contributions.json")
        SQL.add_contributions(records=contributions, session=session)
        session.commit()

        documents = Process.load_json(f"{root}/documents.json")
        SQL.add_documents(records=documents, session=session)
        session.commit()

        indications = Process.load_json(f"{root}/indications.json")
        SQL.add_indications(records=indications, session=session)
        session.commit()

        organizations = Process.load_json(f"{root}/organizations.json")
        SQL.add_organizations(records=organizations, session=session)
        session.commit()

        propositions = Process.load_json(f"{root}/propositions.json")
        SQL.add_propositions(records=propositions, session=session)
        session.commit()

        strengths = Process.load_json(f"{root}/strengths.json")
        SQL.add_strengths(records=strengths, session=session)
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
