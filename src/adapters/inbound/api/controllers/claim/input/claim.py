from generic.api.pydantic_models import CamelCasedAliasesModel


class ClaimCreateSchemaIn(CamelCasedAliasesModel):

    system_number: str


class ClaimUpdateSchemaIn(CamelCasedAliasesModel):

    system_number: str
