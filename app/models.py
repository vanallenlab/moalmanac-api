import configparser
import os
import sqlalchemy
from sqlalchemy.orm import sessionmaker

config = configparser.ConfigParser()
config.read('config.ini')

path = config['database']['path']
path = os.path.abspath(path)
engine = sqlalchemy.create_engine(f"sqlite:///{path}")
#Session = sqlalchemy.orm.sessionmaker(bind=engine)
Session = sessionmaker(bind=engine)


class Base(sqlalchemy.orm.DeclarativeBase):
    pass


class About(Base):
    __tablename__ = "about"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    github = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    label = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    license = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    release = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    url = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    last_updated = sqlalchemy.Column(sqlalchemy.Date, nullable=False)


class Biomarker(Base):
    __tablename__ = "biomarkers"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    biomarker_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    display = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    present = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)

    marker = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    unit = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    equality = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    value = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    gene = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    chromosome = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    start_position = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    end_position = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    reference_allele = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    alternate_allele = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    cdna_change = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    protein_change = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    variant_annotation = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    exon = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    rsid = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    hgvsg = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    hgvsc = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    requires_oncogenic = sqlalchemy.Column(sqlalchemy.Boolean, nullable=True)
    requires_pathogenic = sqlalchemy.Column(sqlalchemy.Boolean, nullable=True)

    gene1 = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    gene2 = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    rearrangement_type = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    locus = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    direction = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    cytoband = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    arm = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    status = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    statements = sqlalchemy.orm.relationship(
        "Statement",
        secondary = "statement_biomarker_association",
        back_populates = "biomarkers",
    )


class Context(Base):
    __tablename__ = "contexts"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    disease = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    display = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    oncotree_code = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    oncotree_term = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    solid_tumor = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)


class Document(Base):
    __tablename__ = 'documents'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    label = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    alternative_labels = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    citation = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    document_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    drug_name_brand = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    drug_name_generic = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    first_published = sqlalchemy.Column(sqlalchemy.Date, nullable=True)
    last_updated = sqlalchemy.Column(sqlalchemy.Date, nullable=False)
    organization = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    publication_date = sqlalchemy.Column(sqlalchemy.Date, nullable=False)
    url = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    url_epar = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    indications = sqlalchemy.orm.relationship(
        "Indication",
        back_populates="document"
    )

    statements = sqlalchemy.orm.relationship(
        "Statement",
        back_populates="document"
    )


class Implication(Base):
    __tablename__ = 'implications'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    implication_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    therapies = sqlalchemy.orm.relationship(
        "Therapy",
        secondary="implication_therapy_association",
        back_populates="implications"
    )
    _therapy = sqlalchemy.Column(sqlalchemy.String, nullable=True)


class Indication(Base):
    __tablename__ = 'indications'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    document_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('documents.id'), nullable=False)
    indication = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    icd10 = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    regimen_code = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    reimbursement_category = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    reimbursement_date = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    reimbursement_details = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    document = sqlalchemy.orm.relationship(
        "Document",
        back_populates="indications"
    )


class Organization(Base):
    __tablename__ = 'organizations'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    label = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    last_updated = sqlalchemy.Column(sqlalchemy.Date, nullable=False)


class Therapy(Base):
    __tablename__ = "therapies"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    therapy_name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    therapy_strategy = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    therapy_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    implications = sqlalchemy.orm.relationship(
        "Implication",
        secondary="implication_therapy_association",
        back_populates="therapies",
    )


class ImplicationTherapyAssociation(Base):
    __tablename__ = "implication_therapy_association"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    implication_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('implications.id'), nullable=False)
    therapy_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('therapies.id'), nullable=False)


class Statement(Base):
    __tablename__ = 'statements'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    document_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('documents.id'), nullable=False)
    biomarkers = sqlalchemy.orm.relationship(
        "Biomarker",
        secondary="statement_biomarker_association",
        back_populates="statements",
    )
    context = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('contexts.id'), nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    evidence = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    implication = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('implications.id'), nullable=False)
    indication = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('indications.id'), nullable=False)
    last_updated = sqlalchemy.Column(sqlalchemy.Date, nullable=False)
    deprecated = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)

    document = sqlalchemy.orm.relationship(
        "Document",
        back_populates="statements"
    )


class StatementBiomarkerAssociation(Base):
    __tablename__ = "statement_biomarker_association"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    statement_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('statements.id'), nullable=False)
    biomarker_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('biomarkers.id'), nullable=False)


Base.metadata.create_all(bind=engine)
