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
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    license = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    release = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    url = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    last_updated = sqlalchemy.Column(sqlalchemy.Date, nullable=False)


class Agents(Base):
    __tablename__ = "agents"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    subtype = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=False)


class Biomarkers(Base):
    __tablename__ = "biomarkers"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    biomarker_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    present = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)

    genes = sqlalchemy.orm.Relationship(
        "Genes",
        secondary="association_biomarkers_and_genes",
        back_populates="biomarkers"
    )

    marker = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    unit = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    equality = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    value = sqlalchemy.Column(sqlalchemy.String, nullable=True)

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

    rearrangement_type = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    locus = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    direction = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    cytoband = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    arm = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    status = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    propositions = sqlalchemy.orm.Relationship(
        "Propositions",
        secondary="association_biomarkers_and_propositions",
        back_populates="biomarkers"
    )


class Codings(Base):
    __tablename__ = "codings"

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    code = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    system = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    systemVersion = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    iris = sqlalchemy.Column(sqlalchemy.String, nullable=True)


class Contributions(Base):
    __tablename__ = "contributions"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    agent_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('agents.id'), nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    date = sqlalchemy.Column(sqlalchemy.Date, nullable=False)

    statements = sqlalchemy.orm.Relationship(
        "Statements",
        secondary="association_contributions_and_statements",
        back_populates="contributions"
    )


class Diseases(Base):
    __tablename__ = "diseases"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    concept_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    primary_coding_id = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey('codings.id'), nullable=False)
    mappings = sqlalchemy.orm.Relationship(
        "Mappings",
        secondary="association_diseases_and_mappings",
        back_populates="diseases"
    )
    solid_tumor = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)


class Documents(Base):
    __tablename__ = 'documents'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    subtype = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    aliases = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    citation = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    company = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    drug_name_brand = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    drug_name_generic = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    first_published = sqlalchemy.Column(sqlalchemy.Date, nullable=True)
    access_date = sqlalchemy.Column(sqlalchemy.Date, nullable=True)
    organization_id = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey('organizations.id'), nullable=False)
    publication_date = sqlalchemy.Column(sqlalchemy.Date, nullable=False)
    url = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    url_epar = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    application_number = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)

    statements = sqlalchemy.orm.Relationship(
        "Statements",
        secondary="association_documents_and_statements",
        back_populates="documents"
    )


class Genes(Base):
    __tablename__ = 'genes'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    concept_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    primary_coding_id = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey('codings.id'), nullable=False)
    mappings = sqlalchemy.orm.Relationship(
        "Mappings",
        secondary="association_genes_and_mappings",
        back_populates="genes"
    )
    location = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    location_sortable = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    biomarkers = sqlalchemy.orm.Relationship(
        "Biomarkers",
        secondary="association_biomarkers_and_genes",
        back_populates="genes"
    )

"""
class Implication(Base):
    __tablename__ = 'implications'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    implication_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    therapy = sqlalchemy.orm.Relationship(
        "Therapy",
        secondary="implication_therapy_association",
        back_populates="implications"
    )
    _therapy = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    statements = sqlalchemy.orm.Relationship(
        "Statement",
        back_populates="implication"
    )
"""


class Indication(Base):
    __tablename__ = 'indications'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    document_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('documents.id'), nullable=False)
    indication = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    initial_approval_date = sqlalchemy.Column(sqlalchemy.Date, nullable=True)
    initial_approval_url = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    raw_biomarkers = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    raw_cancer_type = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    raw_therapeutics = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    icd10 = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    regimen_code = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    reimbursement_category = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    reimbursement_date = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    reimbursement_details = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    date_regular_approval = sqlalchemy.Column(sqlalchemy.Date, nullable=True)
    date_accelerated_approval = sqlalchemy.Column(sqlalchemy.Date, nullable=True)

    """
    document = sqlalchemy.orm.Relationship(
        "Document",
        back_populates="indication"
    )
    statements = sqlalchemy.orm.Relationship(
        "Statement",
        back_populates="indication"
    )
    """


class Mappings(Base):
    __tablename__ = 'mappings'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    primary_coding_id = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey('codings.id'), nullable=False)
    coding_id = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey('codings.id'), nullable=False)
    relation = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    diseases = sqlalchemy.orm.Relationship(
        "Diseases",
        secondary="association_diseases_and_mappings",
        back_populates="mappings"
    )
    genes = sqlalchemy.orm.Relationship(
        "Genes",
        secondary="association_genes_and_mappings",
        back_populates="mappings"
    )
    therapies = sqlalchemy.orm.Relationship(
        "Therapies",
        secondary="association_mappings_and_therapies",
        back_populates="mappings"
    )


class Organization(Base):
    __tablename__ = 'organizations'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    label = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    last_updated = sqlalchemy.Column(sqlalchemy.Date, nullable=False)


class Propositions(Base):
    __tablename__ = 'propositions'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    predicate = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    biomarkers = sqlalchemy.orm.Relationship(
        "Biomarkers",
        secondary="association_biomarkers_and_propositions",
        back_populates="propositions"
    )
    condition_qualifier_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('diseases.id'), nullable=False)
    therapy_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('therapies.id'), nullable=True)
    therapy_group_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('therapy_groups.id'), nullable=True)


class Statements(Base):
    __tablename__ = 'statements'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    contributions = sqlalchemy.orm.Relationship(
        "Contributions",
        secondary="association_contributions_and_statements",
        back_populates="statements"
    )
    documents = sqlalchemy.orm.Relationship(
        "Documents",
        secondary="association_documents_and_statements",
        back_populates="statements"
    )
    proposition_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('propositions.id'), nullable=False)
    direction = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    strength_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('strengths.id'), nullable=False)
    indication_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('indications.id'), nullable=True)


class Strengths(Base):
    __tablename__ = 'strengths'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    concept_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    primary_coding_id = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey('codings.id'), nullable=False)
    # mappings =


class Therapies(Base):
    __tablename__ = "therapies"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    concept_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    primary_coding_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('codings.id'), nullable=False)
    mappings = sqlalchemy.orm.Relationship(
        "Mappings",
        secondary="association_mappings_and_therapies",
        back_populates="therapies"
    )
    therapy_strategy = sqlalchemy.orm.Relationship(
        "TherapyStrategies",
        secondary="association_therapies_and_therapy_strategies",
        back_populates="therapies"
    )
    therapy_strategy_description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    therapy_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    therapy_type_description = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    therapy_groups = sqlalchemy.orm.Relationship(
        "TherapyGroups",
        secondary="association_therapies_and_therapy_groups",
        back_populates="therapies"
    )


class TherapyGroups(Base):
    __tablename__ = "therapy_groups"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    membership_operator = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    therapies = sqlalchemy.orm.Relationship(
        "Therapies",
        secondary="association_therapies_and_therapy_groups",
        back_populates="therapy_groups"
    )


class TherapyStrategies(Base):
    __tablename__ = "therapy_strategies"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    therapies = sqlalchemy.orm.Relationship(
        "Therapies",
        secondary="association_therapies_and_therapy_strategies",
        back_populates="therapy_strategy"
    )


class AssociationBiomarkersAndGenes(Base):
    __tablename__ = "association_biomarkers_and_genes"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    biomarker_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('biomarkers.id'), nullable=False)
    gene_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('genes.id'), nullable=False)


class AssociationBiomarkersAndPropositions(Base):
    __tablename__ = "association_biomarkers_and_propositions"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    biomarker_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('biomarkers.id'), nullable=False)
    proposition_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('propositions.id'), nullable=False)


class AssociationContributionsAndStatements(Base):
    __tablename__ = "association_contributions_and_statements"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    contribution_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('contributions.id'), nullable=False)
    statements_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('statements.id'), nullable=False)


class AssociationDiseasesAndMappings(Base):
    __tablename__ = "association_diseases_and_mappings"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    disease_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('diseases.id'), nullable=False)
    mapping_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('mappings.id'), nullable=False)


class AssociationDocumentsAndStatements(Base):
    __tablename__ = "association_documents_and_statements"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    document_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('documents.id'), nullable=False)
    statement_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('statements.id'), nullable=False)


class AssociationGenesAndMappings(Base):
    __tablename__ = "association_genes_and_mappings"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    gene_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('genes.id'), nullable=False)
    mapping_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('mappings.id'), nullable=False)


class AssociationMappingsAndTherapies(Base):
    __tablename__ = "association_mappings_and_therapies"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    mapping_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('mappings.id'), nullable=False)
    therapy_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('therapies.id'), nullable=False)


class AssociationTherapyAndTherapyGroup(Base):
    __tablename__ = "association_therapies_and_therapy_groups"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    therapy_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('therapies.id'), nullable=False)
    therapy_group_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('therapy_groups.id'), nullable=False)


class AssociationTherapiesAndTherapyStrategies(Base):
    __tablename__ = "association_therapies_and_therapy_strategies"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    therapy_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('therapies.id'), nullable=False)
    therapy_strategy_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('therapy_strategies.id'), nullable=False)


Base.metadata.create_all(bind=engine)
