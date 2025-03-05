from pydantic import BaseModel, Field, GetCoreSchemaHandler
from typing import Optional, Any, Annotated
from bson import ObjectId
from pydantic_core import core_schema


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        """
        We're returning a pydantic_core.CoreSchema that does the following:
        - Validates that the input value is a valid ObjectId string
        - Returns an actual bson.ObjectId instance
        """
        return core_schema.union_schema([
            # First try to interpret the incoming value as a string
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(
                    function=cls.validate
                ),
            ]),
            # If that doesn't work, check if it's already an ObjectId instance
            core_schema.is_instance_schema(ObjectId),
        ])

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


class MongoBaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    model_config = {
        "populate_by_name": True,
        "json_encoders": {
            ObjectId: str
        }
    }