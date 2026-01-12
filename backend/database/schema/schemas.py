from marshmallow import Schema, fields, EXCLUDE, post_load
from backend.database.models import Worker, Entry


class WorkerSchema(Schema):
    class Meta:
        model = Worker
        load_instance = True
        include_fk = True

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    expiration_date = fields.DateTime(required=True)

    @post_load
    def make_metadata(self, data, **kwargs):
        return Worker(**data)


class EntrySchema(Schema):
    class Meta:
        model = Entry
        load_instance=True
        include_fk = True

    id = fields.Int(dump_only=True)
    date = fields.DateTime(dump_only=True)
    worker_id = fields.Int(required=True)
    code = fields.Int(required=True)
    message = fields.Str(required=True)
    face_image = fields.Str(required=True)
