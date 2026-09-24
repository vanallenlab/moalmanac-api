"""
SQLAlchemy models mirroring moalmanac-db/schemas/referenced.

Each entity table has one column per scalar field of its referenced schema, and the
column name is the JSON key. Where the JSON key cannot be a Python attribute
(`hgvs.g`) or would collide with a relationship (`allele`, `location`), the column
keeps the JSON key as its name and is mapped to a different attribute
(`hgvs_g`, `allele_id`, `location_id`).

Array-valued foreign keys (e.g. `genes`, `mappings`, `reportedIn`) are stored in
`_association_*` tables. Each association row has a `position` so that array order
round-trips. Relationships built on association tables are read-only
(`viewonly=True`) and ordered by `position`; the loader writes association rows
directly.
"""

import datetime

import sqlalchemy
import sqlalchemy.orm


class Base(sqlalchemy.orm.DeclarativeBase):
    pass


class About(Base):
    __tablename__ = "about"

    id = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
    )
    github = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    name = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    license = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    release = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    url = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    last_updated = sqlalchemy.Column(
        sqlalchemy.Date,
        nullable=False,
    )


class Agents(Base):
    __tablename__ = "agents"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    type = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    agentType = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    name = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    description = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    last_updated: sqlalchemy.orm.Mapped[datetime.date | None] = (
        sqlalchemy.orm.mapped_column(
            sqlalchemy.Date,
            nullable=True,
        )
    )
    url = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True,
    )

    # Relationships
    contributions = sqlalchemy.orm.Relationship(
        "Contributions",
        back_populates="agent",
    )
    documents = sqlalchemy.orm.Relationship(
        "Documents",
        back_populates="agent",
    )


class Alleles(Base):
    __tablename__ = "alleles"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    type = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    name = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    aliases = sqlalchemy.Column(
        sqlalchemy.JSON,
        nullable=False,
    )
    description = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    digest = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    hgvs_g = sqlalchemy.Column(
        "hgvs.g",
        sqlalchemy.String,
        nullable=True,
    )
    hgvs_c = sqlalchemy.Column(
        "hgvs.c",
        sqlalchemy.String,
        nullable=True,
    )
    hgvs_c_short = sqlalchemy.Column(
        "hgvs.c_short",
        sqlalchemy.String,
        nullable=True,
    )
    hgvs_p = sqlalchemy.Column(
        "hgvs.p",
        sqlalchemy.String,
        nullable=True,
    )
    hgvs_p_short = sqlalchemy.Column(
        "hgvs.p_short",
        sqlalchemy.String,
        nullable=True,
    )
    location_id = sqlalchemy.Column(
        "location",
        sqlalchemy.String,
        sqlalchemy.ForeignKey("sequence_locations.id"),
        nullable=False,
    )
    state_type = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    state_sequence = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    state_length = sqlalchemy.Column(
        sqlalchemy.Integer,
        nullable=True,
    )
    state_repeat_subunit_length = sqlalchemy.Column(
        sqlalchemy.Integer,
        nullable=True,
    )

    # Relationships
    biomarkers = sqlalchemy.orm.Relationship(
        "Biomarkers",
        back_populates="allele",
    )
    location = sqlalchemy.orm.Relationship(
        "SequenceLocations",
    )


class BiomarkerCriteria(Base):
    __tablename__ = "biomarker_criteria"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    subject_id = sqlalchemy.Column(
        "subject",
        sqlalchemy.String,
        sqlalchemy.ForeignKey("biomarkers.id"),
        nullable=False,
    )
    present = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
    )

    # Relationships
    propositions = sqlalchemy.orm.Relationship(
        "Propositions",
        secondary="_association_biomarker_criteria_and_propositions",
        back_populates="biomarker_criteria",
        viewonly=True,
    )
    subject = sqlalchemy.orm.Relationship(
        "Biomarkers",
        back_populates="criteria",
    )


class BiomarkerExtensions(Base):
    """
    One row per item of a biomarker's `extensions` array, in array order.
    """

    __tablename__ = "biomarker_extensions"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        autoincrement=True,
    )
    biomarker_id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("biomarkers.id"),
        nullable=False,
    )
    position = sqlalchemy.Column(
        sqlalchemy.Integer,
        nullable=False,
    )
    name = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    value = sqlalchemy.Column(
        sqlalchemy.JSON,
        nullable=True,
    )
    description = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True,
    )

    # Relationships
    biomarker = sqlalchemy.orm.Relationship(
        "Biomarkers",
        back_populates="extensions",
    )


class Biomarkers(Base):
    __tablename__ = "biomarkers"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    type = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    name = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    allele_id = sqlalchemy.Column(
        "allele",
        sqlalchemy.String,
        sqlalchemy.ForeignKey("alleles.id"),
        nullable=True,
    )
    copy_change_id = sqlalchemy.Column(
        "copyChange",
        sqlalchemy.String,
        sqlalchemy.ForeignKey("copy_changes.id"),
        nullable=True,
    )
    function_id = sqlalchemy.Column(
        "function",
        sqlalchemy.String,
        sqlalchemy.ForeignKey("function_consequences.id"),
        nullable=True,
    )
    biomarker_type = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )

    # Relationships
    allele = sqlalchemy.orm.Relationship(
        "Alleles",
        back_populates="biomarkers",
    )
    copy_change = sqlalchemy.orm.Relationship(
        "CopyChanges",
    )
    criteria = sqlalchemy.orm.Relationship(
        "BiomarkerCriteria",
        back_populates="subject",
    )
    extensions = sqlalchemy.orm.Relationship(
        "BiomarkerExtensions",
        back_populates="biomarker",
        order_by="BiomarkerExtensions.position",
    )
    function = sqlalchemy.orm.Relationship(
        "FunctionConsequences",
    )
    genes = sqlalchemy.orm.Relationship(
        "Genes",
        secondary="_association_biomarkers_and_genes",
        back_populates="biomarkers",
        order_by="AssociationBiomarkersAndGenes.position",
        viewonly=True,
    )
    location = sqlalchemy.orm.Relationship(
        "SequenceLocations",
        secondary="_association_biomarkers_and_sequence_locations",
        order_by="AssociationBiomarkersAndSequenceLocations.position",
        viewonly=True,
    )


class Codings(Base):
    __tablename__ = "codings"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    code = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    name = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True,
    )
    system = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    systemVersion = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True,
    )
    iris = sqlalchemy.Column(
        sqlalchemy.JSON,
        nullable=False,
    )

    # Relationships
    mappings = sqlalchemy.orm.Relationship(
        "Mappings",
        foreign_keys="Mappings.coding_id",
        back_populates="coding",
    )
    primary_mappings = sqlalchemy.orm.Relationship(
        "Mappings",
        foreign_keys="Mappings.primary_coding_id",
        back_populates="primary_coding",
    )


class Contributions(Base):
    __tablename__ = "contributions"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    type = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    agent_id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("agents.id"),
        nullable=False,
    )
    description = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    date = sqlalchemy.Column(
        sqlalchemy.Date,
        nullable=False,
    )

    # Relationships
    agent = sqlalchemy.orm.Relationship(
        "Agents",
        back_populates="contributions",
    )
    indications = sqlalchemy.orm.Relationship(
        "Indications",
        secondary="_association_contributions_and_indications",
        back_populates="contributions",
        viewonly=True,
    )
    statements = sqlalchemy.orm.Relationship(
        "Statements",
        secondary="_association_contributions_and_statements",
        back_populates="contributions",
        viewonly=True,
    )


class CopyChanges(Base):
    __tablename__ = "copy_changes"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    name = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )


class Diseases(Base):
    __tablename__ = "diseases"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    conceptType = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    name = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    primary_coding_id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("codings.id"),
        nullable=False,
    )
    solid_tumor = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
    )

    # Relationships
    mappings = sqlalchemy.orm.Relationship(
        "Mappings",
        secondary="_association_diseases_and_mappings",
        order_by="AssociationDiseasesAndMappings.position",
        viewonly=True,
    )
    primary_coding = sqlalchemy.orm.Relationship(
        "Codings",
    )
    propositions = sqlalchemy.orm.Relationship(
        "Propositions",
        back_populates="condition_qualifier",
    )


class Documents(Base):
    __tablename__ = "documents"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    type = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    documentType = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    name = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    title = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True,
    )
    aliases = sqlalchemy.Column(
        sqlalchemy.JSON,
        nullable=False,
    )
    description = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    doi = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True,
    )
    pmid = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True,
    )
    agent_id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("agents.id"),
        nullable=False,
    )
    company = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    drug_name_brand = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True,
    )
    drug_name_generic = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True,
    )
    first_publication_date: sqlalchemy.orm.Mapped[datetime.date | None] = (
        sqlalchemy.orm.mapped_column(
            sqlalchemy.Date,
            nullable=True,
        )
    )
    # Integer or string (or null) per the schema, so stored as JSON
    identification_number = sqlalchemy.Column(
        sqlalchemy.JSON,
        nullable=True,
    )
    publication_date: sqlalchemy.orm.Mapped[datetime.date | None] = (
        sqlalchemy.orm.mapped_column(
            sqlalchemy.Date,
            nullable=True,
        )
    )
    status = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )

    # Relationships
    agent = sqlalchemy.orm.Relationship(
        "Agents",
        back_populates="documents",
    )
    indications = sqlalchemy.orm.Relationship(
        "Indications",
        secondary="_association_documents_and_indications",
        back_populates="documents",
        viewonly=True,
    )
    statements = sqlalchemy.orm.Relationship(
        "Statements",
        secondary="_association_documents_and_statements",
        back_populates="documents",
        viewonly=True,
    )
    urls = sqlalchemy.orm.Relationship(
        "URLs",
        secondary="_association_documents_and_urls",
        order_by="AssociationDocumentsAndURLs.position",
        viewonly=True,
    )


class FunctionConsequences(Base):
    __tablename__ = "function_consequences"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    name = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    primary_coding_id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("codings.id"),
        nullable=False,
    )

    # Relationships
    primary_coding = sqlalchemy.orm.Relationship(
        "Codings",
    )


class Genes(Base):
    __tablename__ = "genes"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    conceptType = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    name = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    primary_coding_id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("codings.id"),
        nullable=False,
    )
    cds_start = sqlalchemy.Column(
        sqlalchemy.Integer,
        nullable=False,
    )
    location = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    location_sortable = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    protein_product_id = sqlalchemy.Column(
        "protein_product",
        sqlalchemy.String,
        sqlalchemy.ForeignKey("sequence_locations.id"),
        nullable=False,
    )
    transcript_id = sqlalchemy.Column(
        "transcript",
        sqlalchemy.String,
        sqlalchemy.ForeignKey("sequence_locations.id"),
        nullable=False,
    )

    # Relationships
    biomarkers = sqlalchemy.orm.Relationship(
        "Biomarkers",
        secondary="_association_biomarkers_and_genes",
        back_populates="genes",
        viewonly=True,
    )
    mappings = sqlalchemy.orm.Relationship(
        "Mappings",
        secondary="_association_genes_and_mappings",
        order_by="AssociationGenesAndMappings.position",
        viewonly=True,
    )
    primary_coding = sqlalchemy.orm.Relationship(
        "Codings",
    )
    protein_product = sqlalchemy.orm.Relationship(
        "SequenceLocations",
        foreign_keys=[protein_product_id],
    )
    protein_product_exons = sqlalchemy.orm.Relationship(
        "SequenceLocations",
        secondary="_association_genes_and_protein_product_exons",
        order_by="AssociationGenesAndProteinProductExons.position",
        viewonly=True,
    )
    transcript = sqlalchemy.orm.Relationship(
        "SequenceLocations",
        foreign_keys=[transcript_id],
    )
    transcript_exons = sqlalchemy.orm.Relationship(
        "SequenceLocations",
        secondary="_association_genes_and_transcript_exons",
        order_by="AssociationGenesAndTranscriptExons.position",
        viewonly=True,
    )


class Indications(Base):
    __tablename__ = "indications"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    type = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    description = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    status = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    statement_description = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    raw_biomarkers = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True,
    )
    raw_cancer_types = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    raw_therapeutics = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    # HSE indications only; null for every other organization
    reimbursement_scheme = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True,
    )
    reimbursement_comment = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True,
    )

    # Relationships
    contributions = sqlalchemy.orm.Relationship(
        "Contributions",
        secondary="_association_contributions_and_indications",
        back_populates="indications",
        order_by="AssociationContributionsAndIndications.position",
        viewonly=True,
    )
    documents = sqlalchemy.orm.Relationship(
        "Documents",
        secondary="_association_documents_and_indications",
        back_populates="indications",
        order_by="AssociationDocumentsAndIndications.position",
        viewonly=True,
    )
    statements = sqlalchemy.orm.Relationship(
        "Statements",
        back_populates="indication",
    )
    superseded_by = sqlalchemy.orm.Relationship(
        "Indications",
        secondary="_association_indications_and_superseded_by",
        primaryjoin="Indications.id == AssociationIndicationsAndSupersededBy.indication_id",
        secondaryjoin="Indications.id == AssociationIndicationsAndSupersededBy.superseded_by_id",
        order_by="AssociationIndicationsAndSupersededBy.position",
        viewonly=True,
    )


class Mappings(Base):
    __tablename__ = "mappings"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    primary_coding_id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("codings.id"),
        nullable=False,
    )
    coding_id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("codings.id"),
        nullable=False,
    )
    relation = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )

    # Relationships
    coding = sqlalchemy.orm.Relationship(
        "Codings",
        foreign_keys=[coding_id],
        back_populates="mappings",
    )
    primary_coding = sqlalchemy.orm.Relationship(
        "Codings",
        foreign_keys=[primary_coding_id],
        back_populates="primary_mappings",
    )


class Propositions(Base):
    __tablename__ = "propositions"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    type = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    predicate = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    conditionQualifier_id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("diseases.id"),
        nullable=False,
    )
    therapy_id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("therapies.id"),
        nullable=True,
    )
    therapy_group_id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("therapy_groups.id"),
        nullable=True,
    )

    # Relationships
    biomarker_criteria = sqlalchemy.orm.Relationship(
        "BiomarkerCriteria",
        secondary="_association_biomarker_criteria_and_propositions",
        back_populates="propositions",
        order_by="AssociationBiomarkerCriteriaAndPropositions.position",
        viewonly=True,
    )
    condition_qualifier = sqlalchemy.orm.Relationship(
        "Diseases",
        back_populates="propositions",
    )
    statements = sqlalchemy.orm.Relationship(
        "Statements",
        back_populates="proposition",
    )
    therapy = sqlalchemy.orm.Relationship(
        "Therapies",
        back_populates="propositions",
    )
    therapy_group = sqlalchemy.orm.Relationship(
        "TherapyGroups",
        back_populates="propositions",
    )


class SequenceLocations(Base):
    __tablename__ = "sequence_locations"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    type = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    name = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True,
    )
    aliases = sqlalchemy.Column(
        sqlalchemy.JSON,
        nullable=False,
    )
    description = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    digest = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    sequence_reference_id = sqlalchemy.Column(
        "sequenceReference",
        sqlalchemy.String,
        sqlalchemy.ForeignKey("sequence_references.id"),
        nullable=False,
    )
    start = sqlalchemy.Column(
        sqlalchemy.Integer,
        nullable=False,
    )
    end = sqlalchemy.Column(
        sqlalchemy.Integer,
        nullable=False,
    )
    sequence = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True,
    )

    # Relationships
    sequence_reference = sqlalchemy.orm.Relationship(
        "SequenceReferences",
    )


class SequenceReferences(Base):
    __tablename__ = "sequence_references"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    type = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    name = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    aliases = sqlalchemy.Column(
        sqlalchemy.JSON,
        nullable=False,
    )
    description = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    moleculeType = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    refgetAccession = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    residueAlphabet = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )


class Statements(Base):
    __tablename__ = "statements"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    type = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    description = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    proposition_id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("propositions.id"),
        nullable=False,
    )
    direction = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    strength_id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("strengths.id"),
        nullable=False,
    )
    status = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    indication_id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("indications.id"),
        nullable=False,
    )

    # Relationships
    contributions = sqlalchemy.orm.Relationship(
        "Contributions",
        secondary="_association_contributions_and_statements",
        back_populates="statements",
        order_by="AssociationContributionsAndStatements.position",
        viewonly=True,
    )
    documents = sqlalchemy.orm.Relationship(
        "Documents",
        secondary="_association_documents_and_statements",
        back_populates="statements",
        order_by="AssociationDocumentsAndStatements.position",
        viewonly=True,
    )
    indication = sqlalchemy.orm.Relationship(
        "Indications",
        back_populates="statements",
    )
    proposition = sqlalchemy.orm.Relationship(
        "Propositions",
        back_populates="statements",
    )
    strength = sqlalchemy.orm.Relationship(
        "Strengths",
        back_populates="statements",
    )


class Strengths(Base):
    __tablename__ = "strengths"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    conceptType = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    name = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    primary_coding_id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("codings.id"),
        nullable=False,
    )

    # Relationships
    mappings = sqlalchemy.orm.Relationship(
        "Mappings",
        secondary="_association_mappings_and_strengths",
        order_by="AssociationMappingsAndStrengths.position",
        viewonly=True,
    )
    primary_coding = sqlalchemy.orm.Relationship(
        "Codings",
    )
    statements = sqlalchemy.orm.Relationship(
        "Statements",
        back_populates="strength",
    )


class Terms(Base):
    __tablename__ = "terms"

    id = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
    )
    table = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    record_id = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    record_name = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True,
    )
    associated = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
    )


class TermCounts(Base):
    __tablename__ = "term_counts"

    id = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
    )
    table = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    count_associated = sqlalchemy.Column(
        sqlalchemy.Integer,
        nullable=False,
    )
    count_total = sqlalchemy.Column(
        sqlalchemy.Integer,
        nullable=False,
    )


class Therapies(Base):
    __tablename__ = "therapies"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    conceptType = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    name = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )
    primary_coding_id = sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey("codings.id"),
        nullable=False,
    )
    therapy_strategy = sqlalchemy.Column(
        sqlalchemy.JSON,
        nullable=False,
    )
    therapy_type = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )

    # Relationships
    mappings = sqlalchemy.orm.Relationship(
        "Mappings",
        secondary="_association_mappings_and_therapies",
        order_by="AssociationMappingsAndTherapies.position",
        viewonly=True,
    )
    primary_coding = sqlalchemy.orm.Relationship(
        "Codings",
    )
    propositions = sqlalchemy.orm.Relationship(
        "Propositions",
        back_populates="therapy",
    )
    therapy_groups = sqlalchemy.orm.Relationship(
        "TherapyGroups",
        secondary="_association_therapies_and_therapy_groups",
        back_populates="therapies",
        viewonly=True,
    )


class TherapyGroups(Base):
    __tablename__ = "therapy_groups"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    membershipOperator = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )

    # Relationships
    propositions = sqlalchemy.orm.Relationship(
        "Propositions",
        back_populates="therapy_group",
    )
    therapies = sqlalchemy.orm.Relationship(
        "Therapies",
        secondary="_association_therapies_and_therapy_groups",
        back_populates="therapy_groups",
        order_by="AssociationTherapiesAndTherapyGroups.position",
        viewonly=True,
    )


class URLs(Base):
    __tablename__ = "urls"

    # Fields
    id = sqlalchemy.Column(
        sqlalchemy.String,
        primary_key=True,
    )
    url = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
    )


# Association tables
# Each row links an owner record (first foreign key) to one item of one of its
# array-valued fields (second foreign key); `position` is the item's index in the array.


def _association_id() -> sqlalchemy.Column:
    """
    Creates the surrogate primary key column shared by association tables.

    Returns:
        sqlalchemy.Column: An autoincrementing integer primary key column.
    """
    return sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        autoincrement=True,
    )


def _association_position() -> sqlalchemy.Column:
    """
    Creates the array index column shared by association tables.

    Returns:
        sqlalchemy.Column: A non-nullable integer column.
    """
    return sqlalchemy.Column(
        sqlalchemy.Integer,
        nullable=False,
    )


def _foreign_key(target: str) -> sqlalchemy.Column:
    """
    Creates a non-nullable string foreign key column.

    Args:
        target (str): The referenced column, as "table.column".

    Returns:
        sqlalchemy.Column: A non-nullable string column with a foreign key to target.
    """
    return sqlalchemy.Column(
        sqlalchemy.String,
        sqlalchemy.ForeignKey(target),
        nullable=False,
    )


class AssociationBiomarkerCriteriaAndPropositions(Base):
    """
    Propositions.biomarker_criteria
    """

    __tablename__ = "_association_biomarker_criteria_and_propositions"

    id = _association_id()
    proposition_id = _foreign_key("propositions.id")
    biomarker_criterion_id = _foreign_key("biomarker_criteria.id")
    position = _association_position()


class AssociationBiomarkersAndGenes(Base):
    """
    Biomarkers.genes
    """

    __tablename__ = "_association_biomarkers_and_genes"

    id = _association_id()
    biomarker_id = _foreign_key("biomarkers.id")
    gene_id = _foreign_key("genes.id")
    position = _association_position()


class AssociationBiomarkersAndSequenceLocations(Base):
    """
    Biomarkers.location
    """

    __tablename__ = "_association_biomarkers_and_sequence_locations"

    id = _association_id()
    biomarker_id = _foreign_key("biomarkers.id")
    sequence_location_id = _foreign_key("sequence_locations.id")
    position = _association_position()


class AssociationContributionsAndIndications(Base):
    """
    Indications.contributions
    """

    __tablename__ = "_association_contributions_and_indications"

    id = _association_id()
    indication_id = _foreign_key("indications.id")
    contribution_id = _foreign_key("contributions.id")
    position = _association_position()


class AssociationContributionsAndStatements(Base):
    """
    Statements.contributions
    """

    __tablename__ = "_association_contributions_and_statements"

    id = _association_id()
    statement_id = _foreign_key("statements.id")
    contribution_id = _foreign_key("contributions.id")
    position = _association_position()


class AssociationDiseasesAndMappings(Base):
    """
    Diseases.mappings
    """

    __tablename__ = "_association_diseases_and_mappings"

    id = _association_id()
    disease_id = _foreign_key("diseases.id")
    mapping_id = _foreign_key("mappings.id")
    position = _association_position()


class AssociationDocumentsAndIndications(Base):
    """
    Indications.reportedIn
    """

    __tablename__ = "_association_documents_and_indications"

    id = _association_id()
    indication_id = _foreign_key("indications.id")
    document_id = _foreign_key("documents.id")
    position = _association_position()


class AssociationDocumentsAndStatements(Base):
    """
    Statements.reportedIn
    """

    __tablename__ = "_association_documents_and_statements"

    id = _association_id()
    statement_id = _foreign_key("statements.id")
    document_id = _foreign_key("documents.id")
    position = _association_position()


class AssociationDocumentsAndURLs(Base):
    """
    Documents.urls
    """

    __tablename__ = "_association_documents_and_urls"

    id = _association_id()
    document_id = _foreign_key("documents.id")
    url_id = _foreign_key("urls.id")
    position = _association_position()


class AssociationGenesAndMappings(Base):
    """
    Genes.mappings
    """

    __tablename__ = "_association_genes_and_mappings"

    id = _association_id()
    gene_id = _foreign_key("genes.id")
    mapping_id = _foreign_key("mappings.id")
    position = _association_position()


class AssociationGenesAndProteinProductExons(Base):
    """
    Genes.protein_product_exons
    """

    __tablename__ = "_association_genes_and_protein_product_exons"

    id = _association_id()
    gene_id = _foreign_key("genes.id")
    sequence_location_id = _foreign_key("sequence_locations.id")
    position = _association_position()


class AssociationGenesAndTranscriptExons(Base):
    """
    Genes.transcript_exons
    """

    __tablename__ = "_association_genes_and_transcript_exons"

    id = _association_id()
    gene_id = _foreign_key("genes.id")
    sequence_location_id = _foreign_key("sequence_locations.id")
    position = _association_position()


class AssociationIndicationsAndSupersededBy(Base):
    """
    Indications.superseded_by
    """

    __tablename__ = "_association_indications_and_superseded_by"

    id = _association_id()
    indication_id = _foreign_key("indications.id")
    superseded_by_id = _foreign_key("indications.id")
    position = _association_position()


class AssociationMappingsAndStrengths(Base):
    """
    Strengths.mappings
    """

    __tablename__ = "_association_mappings_and_strengths"

    id = _association_id()
    strength_id = _foreign_key("strengths.id")
    mapping_id = _foreign_key("mappings.id")
    position = _association_position()


class AssociationMappingsAndTherapies(Base):
    """
    Therapies.mappings
    """

    __tablename__ = "_association_mappings_and_therapies"

    id = _association_id()
    therapy_id = _foreign_key("therapies.id")
    mapping_id = _foreign_key("mappings.id")
    position = _association_position()


class AssociationTherapiesAndTherapyGroups(Base):
    """
    TherapyGroups.therapies
    """

    __tablename__ = "_association_therapies_and_therapy_groups"

    id = _association_id()
    therapy_group_id = _foreign_key("therapy_groups.id")
    therapy_id = _foreign_key("therapies.id")
    position = _association_position()
