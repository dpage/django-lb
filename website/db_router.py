# This class implements our database router. In this example we're using the
# same router for all Django apps, but we could inspect the app_label (or
# model._meta.app_label) and make decisions on a per app, or even per model
# basis.
#
# We can chain multiple routers by listing them in settings.DATABASE_ROUTERS
#
# Django will fall back to the 'default' database if none of the routers can
# supply a database name (i.e. one of the routing functions returns None)

class DbRouter:
    def db_for_read(self, model, **hints):
        # Reads go to the standby node or pool
        return 'standby'

    def db_for_write(self, model, **hints):
        # Writes always go to the primary node.
        return 'primary'

    def allow_relation(self, obj1, obj2, **hints):
        # We have a fully replicated cluster, so we can allow relationships
        # between objects from different databases
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Only allow migrations on the primary
        return db == 'primary'
