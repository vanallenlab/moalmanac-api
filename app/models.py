import sqlalchemy
from sqlalchemy.orm import DeclarativeBase


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

    # Fields
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    subtype = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    last_updated = sqlalchemy.Column(sqlalchemy.Date, nullable=True)
    url = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    # Relationships
    contributions = sqlalchemy.orm.Relationship(
        "Contributions",
        back_populates="agent",
    )
    documents = sqlalchemy.orm.Relationship(
        "Documents",
        back_populates="organization",
    )


class Biomarkers(Base):
    __tablename__ = "biomarkers"

    # Fields
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    biomarker_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    present = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)

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

    # Relationships
    genes = sqlalchemy.orm.Relationship(
        "Genes",
        secondary="_association_biomarkers_and_genes",
        back_populates="biomarkers",
    )
    propositions = sqlalchemy.orm.Relationship(
        "Propositions",
        secondary="_association_biomarkers_and_propositions",
        back_populates="biomarkers",
    )


class Mappings(Base):
    __tablename__ = "mappings"

    # Fields
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    primary_coding_id = sqlalchemy.Column(
        sqlalchemy.String, sqlalchemy.ForeignKey("codings.id"), nullable=False
    )
    coding_id = sqlalchemy.Column(
        sqlalchemy.String, sqlalchemy.ForeignKey("codings.id"), nullable=False
    )
    relation = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    # Relationships
    primary_coding = sqlalchemy.orm.Relationship(
        "Codings", foreign_keys=[primary_coding_id], back_populates="primary_mappings"
    )
    coding = sqlalchemy.orm.Relationship(
        "Codings", foreign_keys=[coding_id], back_populates="mappings"
    )
    diseases = sqlalchemy.orm.Relationship(
        "Diseases",
        secondary="_association_diseases_and_mappings",
        back_populates="mappings",
    )
    genes = sqlalchemy.orm.Relationship(
        "Genes", secondary="_association_genes_and_mappings", back_populates="mappings"
    )
    therapies = sqlalchemy.orm.Relationship(
        "Therapies",
        secondary="_association_mappings_and_therapies",
        back_populates="mappings",
    )


class Codings(Base):
    __tablename__ = "codings"

    # Fields
    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    code = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    system = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    systemVersion = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    iris = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    # Relationships
    primary_mappings = sqlalchemy.orm.Relationship(
        "Mappings",
        foreign_keys=[Mappings.primary_coding_id],
        back_populates="primary_coding",
    )
    mappings = sqlalchemy.orm.Relationship(
        "Mappings", foreign_keys=[Mappings.coding_id], back_populates="coding"
    )
    diseases = sqlalchemy.orm.Relationship("Diseases", back_populates="primary_coding")
    genes = sqlalchemy.orm.Relationship("Genes", back_populates="primary_coding")
    strengths = sqlalchemy.orm.Relationship(
        "Strengths", back_populates="primary_coding"
    )
    therapies = sqlalchemy.orm.Relationship(
        "Therapies", back_populates="primary_coding"
    )


class Contributions(Base):
    __tablename__ = "contributions"
    field_order = ["id", "type", "agent", "agent_id", "description", "date"]

    # Fields
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    agent_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("agents.id"), nullable=False
    )
    description = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    date = sqlalchemy.Column(sqlalchemy.Date, nullable=False)

    # Relationships
    agent = sqlalchemy.orm.Relationship("Agents", back_populates="contributions")
    statements = sqlalchemy.orm.Relationship(
        "Statements",
        secondary="_association_contributions_and_statements",
        back_populates="contributions",
    )


class Diseases(Base):
    __tablename__ = "diseases"

    # Fields
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    concept_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    primary_coding_id = sqlalchemy.Column(
        sqlalchemy.String, sqlalchemy.ForeignKey("codings.id"), nullable=False
    )
    solid_tumor = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)

    # Relationships
    mappings = sqlalchemy.orm.Relationship(
        "Mappings",
        secondary="_association_diseases_and_mappings",
        back_populates="diseases",
    )
    primary_coding = sqlalchemy.orm.Relationship("Codings", back_populates="diseases")
    propositions = sqlalchemy.orm.Relationship(
        "Propositions", back_populates="condition_qualifier"
    )


class Documents(Base):
    __tablename__ = "documents"

    # Fields
    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    subtype = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    # aliases = sqlalchemy.Column(sqlalchemy.List, nullable=True)
    citation = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    company = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    drug_name_brand = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    drug_name_generic = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    first_published = sqlalchemy.Column(sqlalchemy.Date, nullable=True)
    access_date = sqlalchemy.Column(sqlalchemy.Date, nullable=True)
    agent_id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("agents.id"),
        nullable=False,
    )
    publication_date = sqlalchemy.Column(sqlalchemy.Date, nullable=False)
    url = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    url_drug = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    application_number = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)

    # Relationships
    indications = sqlalchemy.orm.Relationship(
        "Indications",
        back_populates="document",
    )
    organization = sqlalchemy.orm.Relationship(
        "Agents",
        back_populates="documents",
    )
    statements = sqlalchemy.orm.Relationship(
        "Statements",
        secondary="_association_documents_and_statements",
        back_populates="documents",
    )


class Genes(Base):
    __tablename__ = "genes"
    field_order = [
        "id",
        "conceptType",
        "name",
        "primaryCoding",
        "primary_coding_id",
        "mappings",
        "extensions",
    ]

    # Fields
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    concept_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    primary_coding_id = sqlalchemy.Column(
        sqlalchemy.String, sqlalchemy.ForeignKey("codings.id"), nullable=False
    )
    location = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    location_sortable = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    # Relationships
    biomarkers = sqlalchemy.orm.Relationship(
        "Biomarkers",
        secondary="_association_biomarkers_and_genes",
        back_populates="genes",
    )
    mappings = sqlalchemy.orm.Relationship(
        "Mappings", secondary="_association_genes_and_mappings", back_populates="genes"
    )
    primary_coding = sqlalchemy.orm.Relationship("Codings", back_populates="genes")


class Indications(Base):
    __tablename__ = "indications"

    # Fields
    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    document_id = sqlalchemy.Column(
        sqlalchemy.String, sqlalchemy.ForeignKey("documents.id"), nullable=False
    )
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
    reimbursement_date = sqlalchemy.Column(sqlalchemy.Date, nullable=True)
    reimbursement_details = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    date_regular_approval = sqlalchemy.Column(sqlalchemy.Date, nullable=True)
    date_accelerated_approval = sqlalchemy.Column(sqlalchemy.Date, nullable=True)

    # Relationships
    document = sqlalchemy.orm.Relationship("Documents", back_populates="indications")
    statements = sqlalchemy.orm.Relationship("Statements", back_populates="indication")


class Propositions(Base):
    __tablename__ = "propositions"

    # Fields
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    predicate = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    condition_qualifier_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("diseases.id"), nullable=False
    )
    therapy_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("therapies.id"), nullable=True
    )
    therapy_group_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("therapy_groups.id"), nullable=True
    )

    # Relationships
    biomarkers = sqlalchemy.orm.Relationship(
        "Biomarkers",
        secondary="_association_biomarkers_and_propositions",
        back_populates="propositions",
    )
    condition_qualifier = sqlalchemy.orm.Relationship(
        "Diseases", back_populates="propositions"
    )
    statements = sqlalchemy.orm.Relationship("Statements", back_populates="proposition")
    therapy = sqlalchemy.orm.Relationship("Therapies", back_populates="propositions")
    therapy_group = sqlalchemy.orm.Relationship(
        "TherapyGroups", back_populates="propositions"
    )


class Statements(Base):
    __tablename__ = "statements"

    # Fields
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    proposition_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("propositions.id"), nullable=False
    )
    direction = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    strength_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("strengths.id"), nullable=False
    )
    indication_id = sqlalchemy.Column(
        sqlalchemy.String, sqlalchemy.ForeignKey("indications.id"), nullable=True
    )

    # Relationships
    contributions = sqlalchemy.orm.Relationship(
        "Contributions",
        secondary="_association_contributions_and_statements",
        back_populates="statements",
    )
    documents = sqlalchemy.orm.Relationship(
        "Documents",
        secondary="_association_documents_and_statements",
        back_populates="statements",
    )
    indication = sqlalchemy.orm.Relationship("Indications", back_populates="statements")
    proposition = sqlalchemy.orm.Relationship(
        "Propositions", back_populates="statements"
    )
    strength = sqlalchemy.orm.Relationship("Strengths", back_populates="statements")


class Strengths(Base):
    __tablename__ = "strengths"

    # Fields
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    concept_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    primary_coding_id = sqlalchemy.Column(
        sqlalchemy.String, sqlalchemy.ForeignKey("codings.id"), nullable=False
    )
    # mappings =

    # Relationships
    primary_coding = sqlalchemy.orm.Relationship("Codings", back_populates="strengths")
    statements = sqlalchemy.orm.Relationship("Statements", back_populates="strength")


class Terms(Base):
    __tablename__ = "terms"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    table = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    record_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    record_name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    associated = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)


class TermCounts(Base):
    __tablename__ = "term_counts"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    table = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    count_associated = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    count_total = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)


class Therapies(Base):
    __tablename__ = "therapies"

    # Fields
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    concept_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    primary_coding_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("codings.id"), nullable=False
    )
    therapy_strategy_description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    therapy_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    therapy_type_description = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    # Relationships
    mappings = sqlalchemy.orm.Relationship(
        "Mappings",
        secondary="_association_mappings_and_therapies",
        back_populates="therapies",
    )
    primary_coding = sqlalchemy.orm.Relationship("Codings", back_populates="therapies")
    propositions = sqlalchemy.orm.Relationship("Propositions", back_populates="therapy")
    therapy_groups = sqlalchemy.orm.Relationship(
        "TherapyGroups",
        secondary="_association_therapies_and_therapy_groups",
        back_populates="therapies",
    )
    therapy_strategy = sqlalchemy.orm.Relationship(
        "TherapyStrategies",
        secondary="_association_therapies_and_therapy_strategies",
        back_populates="therapies",
    )


class TherapyGroups(Base):
    __tablename__ = "therapy_groups"

    # Fields
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    membership_operator = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    # Relationships
    propositions = sqlalchemy.orm.Relationship(
        "Propositions", back_populates="therapy_group"
    )
    therapies = sqlalchemy.orm.Relationship(
        "Therapies",
        secondary="_association_therapies_and_therapy_groups",
        back_populates="therapy_groups",
    )


class TherapyStrategies(Base):
    __tablename__ = "therapy_strategies"

    # Fields
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    # Relationships
    therapies = sqlalchemy.orm.Relationship(
        "Therapies",
        secondary="_association_therapies_and_therapy_strategies",
        back_populates="therapy_strategy",
    )


class AssociationBiomarkersAndGenes(Base):
    __tablename__ = "_association_biomarkers_and_genes"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    biomarker_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("biomarkers.id"), nullable=False
    )
    gene_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("genes.id"), nullable=False
    )


class AssociationBiomarkersAndPropositions(Base):
    __tablename__ = "_association_biomarkers_and_propositions"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    biomarker_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("biomarkers.id"), nullable=False
    )
    proposition_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("propositions.id"), nullable=False
    )


class AssociationContributionsAndStatements(Base):
    __tablename__ = "_association_contributions_and_statements"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    contribution_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("contributions.id"), nullable=False
    )
    statement_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("statements.id"), nullable=False
    )


class AssociationDiseasesAndMappings(Base):
    __tablename__ = "_association_diseases_and_mappings"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    disease_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("diseases.id"), nullable=False
    )
    mapping_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("mappings.id"), nullable=False
    )


class AssociationDocumentsAndStatements(Base):
    __tablename__ = "_association_documents_and_statements"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    document_id = sqlalchemy.Column(
        sqlalchemy.String, sqlalchemy.ForeignKey("documents.id"), nullable=False
    )
    statement_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("statements.id"), nullable=False
    )


class AssociationGenesAndMappings(Base):
    __tablename__ = "_association_genes_and_mappings"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    gene_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("genes.id"), nullable=False
    )
    mapping_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("mappings.id"), nullable=False
    )


class AssociationMappingsAndTherapies(Base):
    __tablename__ = "_association_mappings_and_therapies"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    mapping_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("mappings.id"), nullable=False
    )
    therapy_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("therapies.id"), nullable=False
    )


class AssociationTherapyAndTherapyGroup(Base):
    __tablename__ = "_association_therapies_and_therapy_groups"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    therapy_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("therapies.id"), nullable=False
    )
    therapy_group_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("therapy_groups.id"), nullable=False
    )


class AssociationTherapiesAndTherapyStrategies(Base):
    __tablename__ = "_association_therapies_and_therapy_strategies"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    therapy_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("therapies.id"), nullable=False
    )
    therapy_strategy_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey("therapy_strategies.id"),
        nullable=False,
    )
