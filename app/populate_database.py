import argparse
import json
import os
import typing

import pandas
import sqlalchemy
import sqlalchemy.orm

from app import database, models, referenced


class Process:
    @staticmethod
    def load_json(file: str) -> typing.Any:
        """
        Loads JSON data from a file path.

        Args:
            file (str): The path to the JSON file.

        Returns:
            typing.Any: The deserialized JSON content.
        """
        with open(file) as fp:
            data = json.load(fp)
        return data


class SQL:
    @staticmethod
    def add_about(record: dict, session: sqlalchemy.orm.Session) -> None:
        """
        Inserts the About row into the database from referenced/about.json.

        Args:
            record (dict): The about record.
            session (sqlalchemy.orm.Session): The database session to add the record to.
        """
        session.execute(
            sqlalchemy.insert(models.About.__table__),
            [referenced.about_to_row(record)],
        )

    @staticmethod
    def add_table(
        name: str,
        records: list[dict],
        session: sqlalchemy.orm.Session,
    ) -> None:
        """
        Inserts one referenced table's records, in file order, followed by the rows
        of its association (and extension) tables. Column mapping comes from
        app.referenced.TABLES.

        Args:
            name (str): The referenced table name, a key of referenced.TABLES.
            records (list[dict]): The records from referenced/<name>.json.
            session (sqlalchemy.orm.Session): The database session to add records to.
        """
        rows, children = referenced.records_to_rows(name=name, records=records)
        model = referenced.TABLES[name].model
        if rows:
            session.execute(sqlalchemy.insert(model.__table__), rows)
        for child_model, child_rows in children.items():
            if child_rows:
                session.execute(sqlalchemy.insert(child_model.__table__), child_rows)

    @staticmethod
    def add_term_counts(records: list[dict], session: sqlalchemy.orm.Session) -> None:
        """
        Inserts TermCounts records into the database.

        Args:
            records (list[dict]): A list of term count records to insert.
            session (sqlalchemy.orm.Session): The database session to add records to.
        """
        for record in records:
            count = models.TermCounts(
                id=record.get("id"),
                table=record.get("table"),
                count_associated=record.get("count_associated"),
                count_total=record.get("count_total"),
            )
            session.add(count)

    @staticmethod
    def add_terms(records: list[dict], session: sqlalchemy.orm.Session) -> None:
        """
        Inserts Terms records into the database.

        Args:
            records (list[dict]): A list of term records to insert.
            session (sqlalchemy.orm.Session): The database session to add records to.
        """
        for record in records:
            term = models.Terms(
                id=record.get("id"),
                table=record.get("table"),
                record_id=record.get("record_id"),
                record_name=record.get("record_name"),
                associated=record.get("associated"),
            )
            session.add(term)


class Summary:
    @staticmethod
    def agents(session: sqlalchemy.orm.Session) -> tuple[set, list]:
        """
        Returns the ids of Agents associated with at least one Statement (via the
        Documents the Statement is reported in) and the total set of Agents.

        Args:
            session (sqlalchemy.orm.Session): The database session to query against.

        Returns:
            tuple[set, list]: The associated ids and all Agents instances.
        """
        associated = session.scalars(
            sqlalchemy.select(models.Agents.id)
            .join(models.Documents, models.Documents.agent_id == models.Agents.id)
            .join(
                models.AssociationDocumentsAndStatements,
                models.AssociationDocumentsAndStatements.document_id
                == models.Documents.id,
            ),
        ).all()
        total = session.scalars(sqlalchemy.select(models.Agents)).all()
        return set(associated), total

    @classmethod
    def biomarkers(cls, session: sqlalchemy.orm.Session) -> tuple[set, list]:
        """
        Returns the ids of Biomarkers associated with at least one Statement (via
        Biomarker Criteria and Propositions) and the total set of Biomarkers.

        Args:
            session (sqlalchemy.orm.Session): The database session to query against.

        Returns:
            tuple[set, list]: The associated ids and all Biomarkers instances.
        """
        associated = session.scalars(
            cls.join_biomarkers_to_statements(sqlalchemy.select(models.Biomarkers.id)),
        ).all()
        total = session.scalars(sqlalchemy.select(models.Biomarkers)).all()
        return set(associated), total

    @staticmethod
    def count_terms(records: list[dict]) -> list[dict]:
        """
        Computes total and associated term counts grouped by table.

        Args:
            records (list[dict]): Term records, each containing a `table` and an
                `associated` boolean.

        Returns:
            list[dict]: A list of dictionaries with `table`, `count_associated`,
            and `count_total` keys for each table.
        """
        counts = []
        records = pandas.DataFrame(records)
        for label, group in records.groupby("table"):
            count_total = group.shape[0]
            count_associated = group[group["associated"].eq(True)].shape[0]
            counts.append(
                {
                    "table": label,
                    "count_associated": count_associated,
                    "count_total": count_total,
                },
            )
        return counts

    @staticmethod
    def diseases(session: sqlalchemy.orm.Session) -> tuple[set, list]:
        """
        Returns the ids of Diseases associated with at least one Statement (via
        Propositions) and the total set of Diseases.

        Args:
            session (sqlalchemy.orm.Session): The database session to query against.

        Returns:
            tuple[set, list]: The associated ids and all Diseases instances.
        """
        associated = session.scalars(
            sqlalchemy.select(models.Diseases.id)
            .join(
                models.Propositions,
                models.Propositions.conditionQualifier_id == models.Diseases.id,
            )
            .join(
                models.Statements,
                models.Statements.proposition_id == models.Propositions.id,
            ),
        ).all()
        total = session.scalars(sqlalchemy.select(models.Diseases)).all()
        return set(associated), total

    @staticmethod
    def documents(session: sqlalchemy.orm.Session) -> tuple[set, list]:
        """
        Returns the ids of Documents associated with at least one Statement and the
        total set of Documents.

        Args:
            session (sqlalchemy.orm.Session): The database session to query against.

        Returns:
            tuple[set, list]: The associated ids and all Documents instances.
        """
        associated = session.scalars(
            sqlalchemy.select(models.AssociationDocumentsAndStatements.document_id),
        ).all()
        total = session.scalars(sqlalchemy.select(models.Documents)).all()
        return set(associated), total

    @classmethod
    def genes(cls, session: sqlalchemy.orm.Session) -> tuple[set, list]:
        """
        Returns the ids of Genes associated with at least one Statement (via
        Biomarkers, Biomarker Criteria, and Propositions) and the total set of Genes.

        Args:
            session (sqlalchemy.orm.Session): The database session to query against.

        Returns:
            tuple[set, list]: The associated ids and all Genes instances.
        """
        statement = sqlalchemy.select(
            models.AssociationBiomarkersAndGenes.gene_id,
        ).join(
            models.Biomarkers,
            models.Biomarkers.id == models.AssociationBiomarkersAndGenes.biomarker_id,
        )
        associated = session.scalars(cls.join_biomarkers_to_statements(statement)).all()
        total = session.scalars(sqlalchemy.select(models.Genes)).all()
        return set(associated), total

    @staticmethod
    def indications(session: sqlalchemy.orm.Session) -> tuple[set, list]:
        """
        Returns the ids of Indications associated with at least one Statement and
        the total set of Indications.

        Args:
            session (sqlalchemy.orm.Session): The database session to query against.

        Returns:
            tuple[set, list]: The associated ids and all Indications instances.
        """
        associated = session.scalars(
            sqlalchemy.select(models.Statements.indication_id),
        ).all()
        total = session.scalars(sqlalchemy.select(models.Indications)).all()
        return set(associated), total

    @staticmethod
    def join_biomarkers_to_statements(
        statement: sqlalchemy.Select,
    ) -> sqlalchemy.Select:
        """
        Joins a statement that already includes Biomarkers through Biomarker
        Criteria and Propositions to Statements.

        Args:
            statement (sqlalchemy.Select): A select that includes models.Biomarkers.

        Returns:
            sqlalchemy.Select: The statement joined to models.Statements.
        """
        return (
            statement.join(
                models.BiomarkerCriteria,
                models.BiomarkerCriteria.subject_id == models.Biomarkers.id,
            )
            .join(
                models.AssociationBiomarkerCriteriaAndPropositions,
                models.AssociationBiomarkerCriteriaAndPropositions.biomarker_criterion_id
                == models.BiomarkerCriteria.id,
            )
            .join(
                models.Statements,
                models.Statements.proposition_id
                == models.AssociationBiomarkerCriteriaAndPropositions.proposition_id,
            )
        )

    @classmethod
    def list_terms(cls, session: sqlalchemy.orm.Session) -> list[dict]:
        """
        Lists every record across the supported tables and flags whether each is
        associated with at least one Statement, via the appropriate join path.

        Args:
            session (sqlalchemy.orm.Session): The database session to query against.

        Returns:
            list[dict]: A list of dictionaries describing each record with `id`,
            `table`, `record_id`, `record_name`, and `associated` keys.
        """
        functions = [
            cls.agents,
            cls.biomarkers,
            cls.diseases,
            cls.documents,
            cls.genes,
            cls.indications,
            cls.propositions,
            cls.statements,
            cls.strengths,
            cls.therapies,
        ]
        results = []
        count = 0
        for function in functions:
            associated, total = function(session=session)
            for record in total:
                results.append(
                    {
                        "id": count,
                        "table": function.__name__,
                        "record_id": record.id,
                        "record_name": getattr(record, "name", None),
                        "associated": record.id in associated,
                    },
                )
                count += 1
        return results

    @staticmethod
    def propositions(session: sqlalchemy.orm.Session) -> tuple[set, list]:
        """
        Returns the ids of Propositions associated with at least one Statement and
        the total set of Propositions.

        Args:
            session (sqlalchemy.orm.Session): The database session to query against.

        Returns:
            tuple[set, list]: The associated ids and all Propositions instances.
        """
        associated = session.scalars(
            sqlalchemy.select(models.Statements.proposition_id),
        ).all()
        total = session.scalars(sqlalchemy.select(models.Propositions)).all()
        return set(associated), total

    @staticmethod
    def statements(session: sqlalchemy.orm.Session) -> tuple[set, list]:
        """
        Returns the ids of Statements considered associated and the total set of
        Statements. Every Statement is treated as associated.

        Args:
            session (sqlalchemy.orm.Session): The database session to query against.

        Returns:
            tuple[set, list]: The associated ids and all Statements instances.
        """
        total = session.scalars(sqlalchemy.select(models.Statements)).all()
        return {statement.id for statement in total}, total

    @staticmethod
    def strengths(session: sqlalchemy.orm.Session) -> tuple[set, list]:
        """
        Returns the ids of Strengths associated with at least one Statement and the
        total set of Strengths.

        Args:
            session (sqlalchemy.orm.Session): The database session to query against.

        Returns:
            tuple[set, list]: The associated ids and all Strengths instances.
        """
        associated = session.scalars(
            sqlalchemy.select(models.Statements.strength_id),
        ).all()
        total = session.scalars(sqlalchemy.select(models.Strengths)).all()
        return set(associated), total

    @staticmethod
    def therapies(session: sqlalchemy.orm.Session) -> tuple[set, list]:
        """
        Returns the ids of Therapies associated with at least one Statement, joined
        either directly via Propositions.therapy_id or indirectly via TherapyGroups,
        and the total set of Therapies.

        Args:
            session (sqlalchemy.orm.Session): The database session to query against.

        Returns:
            tuple[set, list]: The associated ids and all Therapies instances.
        """
        therapies_via_propositions = sqlalchemy.select(
            models.Propositions.therapy_id,
        ).join(
            models.Statements,
            models.Statements.proposition_id == models.Propositions.id,
        )
        therapies_via_therapy_groups = (
            sqlalchemy.select(models.AssociationTherapiesAndTherapyGroups.therapy_id)
            .join(
                models.Propositions,
                models.Propositions.therapy_group_id
                == models.AssociationTherapiesAndTherapyGroups.therapy_group_id,
            )
            .join(
                models.Statements,
                models.Statements.proposition_id == models.Propositions.id,
            )
        )
        associated = session.scalars(
            sqlalchemy.union(therapies_via_propositions, therapies_via_therapy_groups),
        ).all()
        total = session.scalars(sqlalchemy.select(models.Therapies)).all()
        return set(associated), total


def main(referenced_directory: str, config_path: str = "config.ini") -> None:
    """
    Loads the moalmanac-db referenced JSON files into the SQLite database named in
    the config file.

    Tables are loaded in the order of app.referenced.TABLES, which satisfies foreign
    keys (enforced on every connection). Term inventory and counts are computed and
    persisted at the end. On error, the session is rolled back and the error is
    re-raised.

    Args:
        referenced_directory (str): The path to the directory containing the
            referenced moalmanac-db JSON files.
        config_path (str): The path to the application configuration file (default: "config.ini").

    Raises:
        FileExistsError: If the database file already exists.
    """
    config = database.read_config_ini(path=config_path)
    database_path = config["database"]["path"]
    if os.path.exists(database_path):
        raise FileExistsError(
            f"{database_path} already exists; remove it before populating.",
        )

    engine, session_factory = database.init_db(config_path=config_path)
    models.Base.metadata.create_all(bind=engine)
    session = session_factory()
    try:
        about = Process.load_json(f"{referenced_directory}/about.json")
        SQL.add_about(record=about, session=session)
        session.commit()

        for name in referenced.TABLES:
            records = Process.load_json(f"{referenced_directory}/{name}.json")
            SQL.add_table(name=name, records=records, session=session)
            session.commit()

        terms = Summary.list_terms(session=session)
        SQL.add_terms(records=terms, session=session)
        session.commit()

        terms_count = Summary.count_terms(records=terms)
        SQL.add_term_counts(records=terms_count, session=session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        prog="Create MOAlmanac SQLite3 file from referenced JSONs",
        description="Using referenced JSON files, create SQLite3 db",
    )
    arg_parser.add_argument(
        "--input",
        "-i",
        default="moalmanac-db/referenced",
        help="Directory for referenced moalmanac db json files",
    )
    arg_parser.add_argument(
        "--config",
        "-c",
        default="config.ini",
        help="Path to config file",
    )
    args = arg_parser.parse_args()

    main(referenced_directory=args.input, config_path=args.config)
