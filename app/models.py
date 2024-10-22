import flask_sqlalchemy
import sqlalchemy

DATABASE_URL = "sqlite:///moalmanac.sqlite3"
engine = sqlalchemy.create_engine(DATABASE_URL)
Session = sqlalchemy.orm.sessionmaker(bind=engine)


class Base(sqlalchemy.orm.DeclarativeBase):
    pass



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
        back_populates="document",
        cascade="all, delete, delete-orphan"
    )


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

    document = sqlalchemy.orm.relationship("Document", back_populates="indications")


Base.metadata.create_all(bind=engine)
