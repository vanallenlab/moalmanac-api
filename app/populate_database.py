import argparse
import datetime
import flask
import json
import pandas
import sqlalchemy
import typing
from . import create_app
from . import models

from sqlalchemy.orm import sessionmaker


class Process:
    @staticmethod
    def load_json(file):
        with open(file) as fp:
            data = json.load(fp)
        return data

    @staticmethod
    def parse_date(date_string, date_string_format='%Y-%m-%d'):
        if isinstance(date_string, str):
            try:
                date_object = datetime.datetime.strptime(date_string, date_string_format)
                return date_object.date()
            except ValueError:
                return None
        else:
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

    @classmethod
    def add_agents(cls, records, session):
        for record in records:
            agent = models.Agents(
                id=record.get('id'),
                type=record.get('type'),
                subtype=record.get('subtype'),
                name=record.get('name'),
                description=record.get('description')
            )
            session.add(agent)

    @classmethod
    def add_biomarkers(cls, records, session):
        for record in records:
            moalmanac_representation = {}
            for item in record.get('extensions'):
                moalmanac_representation[item.get('name')] = item.get('value')

            gene_instances = cls.get_list_instances(
                record=record,
                key='genes',
                session=session,
                model=models.Genes
            )

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

    @classmethod
    def add_codings(cls, records, session):
        for record in records:
            coding = models.Codings(
                id=record.get('id'),
                code=record.get('code'),
                name=record.get('name'),
                system=record.get('system'),
                systemVersion=record.get('systemVersion'),
                iris=record.get('iris')[0]  # This will be a list, eventually
            )
            session.add(coding)

    @classmethod
    def add_contributions(cls, records, session):
        for record in records:
            contribution = models.Contributions(
                id=record.get('id'),
                type=record.get('type'),
                agent_id=record.get('agent_id'),
                description=record.get('description'),
                date=Process.parse_date(record.get('date'))
            )
            session.add(contribution)

    @classmethod
    def add_diseases(cls, records, session):
        for record in records:
            mapping_instances = cls.get_list_instances(
                record=record,
                key='mappings',
                session=session,
                model=models.Mappings
            )
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

    @classmethod
    def add_documents(cls, records, session):
        for record in records:
            document = models.Documents(
                id=record.get('id'),
                type=record.get('type'),
                subtype=record.get('subtype'),
                name=record.get('name'),
                #  aliases=record.get('aliases', None),
                citation=record.get('citation', None),
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

    @classmethod
    def add_genes(cls, records, session):
        for record in records:
            mapping_instances = cls.get_list_instances(
                record=record,
                key='mappings',
                session=session,
                model=models.Mappings
            )
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

    @classmethod
    def add_indications(cls, records, session):
        for record in records:
            reimbursement_date = record.get('reimbursement_date', None)
            if reimbursement_date:
                reimbursement_date = Process.parse_date(reimbursement_date)

            initial_approval_date = record.get('initial_approval_date', None)
            if initial_approval_date:
                initial_approval_date = Process.parse_date(initial_approval_date)

            date_regular_approval = record.get('date_regular_approval', None)
            if date_regular_approval:
                date_regular_approval = Process.parse_date(date_regular_approval)

            date_accelerated_approval = record.get('date_accelerated_approval', None)
            if date_accelerated_approval:
                date_accelerated_approval = Process.parse_date(date_accelerated_approval)

            indication = models.Indications(
                id=record.get('id'),
                document_id=record.get('document_id'),
                indication=record.get('indication'),
                icd10=record.get('icd10'),
                regimen_code=record.get('regimen_code'),
                reimbursement_category=record.get('reimbursement_category'),
                reimbursement_date=reimbursement_date,
                reimbursement_details=record.get('reimbursement_details'),
                description=record.get('description', None),
                initial_approval_date=initial_approval_date,
                initial_approval_url=record.get('initial_approval_url', None),
                raw_biomarkers=record.get('raw_biomarkers', None),
                raw_therapeutics=record.get('raw_therapeutics', None),
                raw_cancer_type=record.get('raw_cancer_type', None),
                date_regular_approval=date_regular_approval,
                date_accelerated_approval=date_accelerated_approval
            )
            session.add(indication)

    @classmethod
    def add_mappings(cls, records, session):
        for record in records:
            mapping = models.Mappings(
                id=record.get('id'),
                primary_coding_id=record.get('primary_coding_id'),
                coding_id=record.get('coding_id'),
                relation=record.get('relation')
            )
            session.add(mapping)

    @classmethod
    def add_organizations(cls, records, session):
        for record in records:
            organization = models.Organizations(
                id=record['id'],
                name=record.get('name'),
                description=record.get('description'),
                url=record.get('url'),
                last_updated=Process.parse_date(record.get('last_updated'))
            )
            session.add(organization)

    @classmethod
    def add_propositions(cls, records, session):
        for record in records:
            biomarker_instances = cls.get_list_instances(
                record=record,
                key='biomarkers',
                session=session,
                model=models.Biomarkers
            )

            proposition = models.Propositions(
                id=record.get('id'),
                type=record.get('type'),
                predicate=record.get('predicate'),
                biomarkers=biomarker_instances,
                condition_qualifier_id=record.get('conditionQualifier_id'),
                therapy_id=record.get('therapy_id'),
                therapy_group_id=record.get('therapy_group_id')
            )
            session.add(proposition)

    @classmethod
    def add_statements(cls, records, session):
        for record in records:
            contribution_instances = cls.get_list_instances(
                record=record,
                key='contributions',
                session=session,
                model=models.Contributions
            )
            document_instances = cls.get_list_instances(
                record=record,
                key='reportedIn',
                session=session,
                model=models.Documents
            )

            statement = models.Statements(
                id=record['id'],
                type=record.get('type'),
                description=record.get('description'),
                contributions=contribution_instances,
                documents=document_instances,
                proposition_id=record.get('proposition_id'),
                direction=record.get('direction'),
                strength_id=record.get('strength_id'),
                indication_id=record.get('indication_id')
            )
            session.add(statement)

    @classmethod
    def add_strengths(cls, records, session):
        for record in records:
            #mapping_ids = record.get('mappings', [])
            #if mapping_ids:
            #    mapping_instances = models.Mappings.query.filter(models.Mappings.id.in_(mapping_ids)).all()
            #else:
            #    mapping_instances = []

            strength = models.Strengths(
                id=record.get('id'),
                concept_type=record.get('conceptType'),
                name=record.get('name'),
                primary_coding_id=record.get('primary_coding_id')
                #    mappings=mapping_instances
            )
            session.add(strength)

    @classmethod
    def add_terms(cls, records, session):
        for record in records:
            term = models.Terms(
                id=record.get('id'),
                table=record.get('table'),
                record_id=record.get('record_id'),
                record_name=record.get('record_name'),
                associated=record.get('associated')
            )
            session.add(term)

    @classmethod
    def add_term_counts(cls, records, session):
        for record in records:
            count = models.TermCounts(
                id=record.get('id'),
                table=record.get('table'),
                count_associated=record.get('count_associated'),
                count_total=record.get('count_total')
            )
            session.add(count)

    @classmethod
    def add_therapies(cls, records, session):
        for record in records:
            mapping_instances = cls.get_list_instances(
                record=record,
                key='mappings',
                session=session,
                model=models.Mappings
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

    @classmethod
    def add_therapy_groups(cls, records, session):
        for record in records:
            therapy_instances = cls.get_list_instances(
                record=record,
                key='therapies',
                session=session,
                model=models.Therapies
            )

            therapy_group = models.TherapyGroups(
                id=record.get('id'),
                membership_operator=record.get('membershipOperator'),
                therapies=therapy_instances
            )
            session.add(therapy_group)

    @staticmethod
    def get_list_instances(record: dict, key: str, session: sqlalchemy.orm.Session, model: typing.Type[models.Base]):
        id_values = record.get(key, [])
        if id_values:
            instances = (
                session
                .query(model)
                .filter(model.id.in_(id_values))
                .all()
            )
        else:
            instances = []
        return instances


class Summary:
    @staticmethod
    def count_terms(records):
        counts = []
        records = pandas.DataFrame(records)
        for label, group in records.groupby('table'):
            count_total = group.shape[0]
            count_associated = group[group['associated'].eq(True)].shape[0]
            counts.append({
                'table': label,
                'count_associated': count_associated,
                'count_total': count_total
            })
        return counts

    @classmethod
    def list_terms(cls, session: sqlalchemy.orm.Session) -> list:
        # Total and associated counts for each table
        functions = [
            cls.biomarkers,
            cls.diseases,
            cls.documents,
            cls.genes,
            cls.indications,
            cls.organizations,
            cls.propositions,
            cls.statements,
            cls.strengths,
            cls.therapies
        ]
        results = []
        count = 0
        for function in functions:
            associated, total = function(session=session)
            for record in total:
                result = {
                    'id': count,
                    'table': function.__name__,
                    'record_id': record.id,
                    'record_name': getattr(record, 'name', None),
                    'associated': True if record in associated else False
                }
                results.append(result)
                count += 1
        return results

    @staticmethod
    def biomarkers(session: sqlalchemy.orm.Session) -> tuple:
        associated = (
            session
            .query(models.Biomarkers)
            .join(
                models.AssociationBiomarkersAndPropositions,
                models.Biomarkers.id == models.AssociationBiomarkersAndPropositions.biomarker_id
            )
            .join(
                models.Propositions,
                models.Propositions.id == models.AssociationBiomarkersAndPropositions.proposition_id
            )
            .join(
                models.Statements,
                models.Statements.proposition_id == models.Propositions.id
            )
            .all()
        )
        total = (
            session
            .query(models.Biomarkers)
            .all()
        )
        return associated, total

    @staticmethod
    def diseases(session: sqlalchemy.orm.Session) -> tuple:
        associated = (
            session
            .query(models.Diseases)
            .join(
                models.Propositions,
                models.Diseases.id == models.Propositions.condition_qualifier_id
            )
            .join(
                models.Statements,
                models.Statements.proposition_id == models.Propositions.id
            )
            .all()
        )
        total = (
            session
            .query(models.Diseases)
            .all()
        )
        return associated, total

    @staticmethod
    def documents(session: sqlalchemy.orm.Session) -> tuple:
        associated = (
            session
            .query(models.Documents)
            .join(
                models.AssociationDocumentsAndStatements,
                models.Documents.id == models.AssociationDocumentsAndStatements.document_id
            )
            .join(
                models.Statements,
                models.Statements.id == models.AssociationDocumentsAndStatements.statement_id
            )
            .all()
        )
        total = (
            session
            .query(models.Documents)
            .all()
        )
        return associated, total

    @staticmethod
    def genes(session: sqlalchemy.orm.Session) -> tuple:
        associated = (
            session
            .query(models.Genes)
            .join(
                models.AssociationBiomarkersAndGenes,
                models.AssociationBiomarkersAndGenes.gene_id == models.Genes.id
            )
            .join(
                models.Biomarkers,
                models.Biomarkers.id == models.AssociationBiomarkersAndGenes.biomarker_id
            )
            .join(
                models.AssociationBiomarkersAndPropositions,
                models.AssociationBiomarkersAndPropositions.biomarker_id == models.Biomarkers.id
            )
            .join(
                models.Propositions,
                models.Propositions.id == models.AssociationBiomarkersAndPropositions.proposition_id,
            )
            .join(
                models.Statements,
                models.Statements.proposition_id == models.Propositions.id
            )
            .all()
        )
        total = (
            session
            .query(models.Genes)
            .all()
        )
        return associated, total

    @staticmethod
    def indications(session: sqlalchemy.orm.Session) -> tuple:
        associated = (
            session
            .query(models.Indications)
            .join(
                models.Statements,
                models.Statements.indication_id == models.Indications.id
            )
            .all()
        )
        total = (
            session
            .query(models.Indications)
            .all()
        )
        return associated, total

    @staticmethod
    def organizations(session: sqlalchemy.orm.Session) -> tuple:
        associated = (
            session
            .query(models.Organizations)
            .join(
                models.Documents,
                models.Documents.organization_id == models.Organizations.id
            )
            .join(
                models.AssociationDocumentsAndStatements,
                models.AssociationDocumentsAndStatements.document_id == models.Documents.id
            )
            .join(
                models.Statements,
                models.Statements.id == models.AssociationDocumentsAndStatements.statement_id
            )
            .all()
        )
        total = (
            session
            .query(models.Organizations)
            .all()
        )
        return associated, total

    @staticmethod
    def propositions(session: sqlalchemy.orm.Session) -> tuple:
        associated = (
            session
            .query(models.Propositions)
            .join(
                models.Statements,
                models.Statements.proposition_id == models.Propositions.id
            )
            .all()
        )
        total = (
            session
            .query(models.Propositions)
            .all()
        )
        return associated, total

    @staticmethod
    def statements(session: sqlalchemy.orm.Session) -> tuple:
        associated = (
            session
            .query(models.Statements)
            .all()
        )
        total = (
            session
            .query(models.Statements)
            .all()
        )
        return associated, total

    @staticmethod
    def strengths(session: sqlalchemy.orm.Session) -> tuple:
        associated = (
            session
            .query(models.Strengths)
            .join(
                models.Statements,
                models.Statements.strength_id == models.Strengths.id
            )
            .all()
        )
        total = (
            session
            .query(models.Strengths)
            .all()
        )
        return associated, total

    @staticmethod
    def therapies(session: sqlalchemy.orm.Session) -> tuple:
        therapies_via_propositions = (
            session
            .query(models.Therapies.id.label('therapy_id'))
            .join(
                models.Propositions,
                models.Propositions.therapy_id == models.Therapies.id
            )
            .join(
                models.Statements,
                models.Statements.proposition_id == models.Propositions.id
            )
        )
        therapies_via_therapy_groups = (
            session
            .query(models.Therapies.id.label('therapy_id'))
            .join(
                models.AssociationTherapyAndTherapyGroup,
                models.AssociationTherapyAndTherapyGroup.therapy_id == models.Therapies.id
            )
            .join(
                models.TherapyGroups,
                models.TherapyGroups.id == models.AssociationTherapyAndTherapyGroup.therapy_group_id
            )
            .join(
                models.Propositions,
                models.Propositions.therapy_group_id == models.TherapyGroups.id
            )
            .join(
                models.Statements,
                models.Statements.proposition_id == models.Propositions.id
            )
        )

        union = (
            sqlalchemy
            .union_all(therapies_via_propositions, therapies_via_therapy_groups)
            .alias('union')
        )
        associated = (
            session
            .query(union.c.therapy_id)
            .all()
        )
        total = (
            session
            .query(models.Therapies.id)
            .all()
        )
        return associated, total


def main(referenced_dictionary, config_path='config.ini'):
    app = create_app(config_path=config_path)
    with app.app_context():
        session = flask.current_app.config['SESSION']()
        try:
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

            terms = Summary.list_terms(session=session)
            SQL.add_terms(records=terms, session=session)
            session.commit()

            terms_count = Summary.count_terms(records=terms)
            SQL.add_term_counts(records=terms_count, session=session)
            session.commit()
            print(terms_count)

        except Exception as e:
            print(f"Error occurred: {e}")
            session.rollback()
        finally:
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
        default='moalmanac-db/referenced',
        help='Directory for referenced moalmanac db json files'
    )
    arg_parser.add_argument(
        '--config',
        '-c',
        default='config.ini',
        help='Path to config file'
    )
    args = arg_parser.parse_args()

    main(
        referenced_dictionary=args.input
    )
