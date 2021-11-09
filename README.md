# django-lb

This is an example application intended to illustrate how a database router can
be utilised in a Django application to route database changes to the primary in
a PostgreSQL cluster, whilst routing all read-only queries to a load balancer
pool over the standby servers in the cluster.

## Anonymous Message Server

The demo application is based on a toy feature I added to a fun website that I 
used to maintain back in the early 90's, in times when there were no frameworks
and writing any kind of application on a website required doing absolutely 
everything in a CGI-BIN script or program. In my case, I used C on DEC OS/F.

The website was called Hmmmmmmm!!! (7 m's and 3 bangs!), and was listed on Yahoo 
when it was just a single page of links. It was hosted at the Department of 
Particle and Nuclear Physics (and later Engineering Science) at Oxford 
University, and featured film and pub reviews, and a variety of gadgets for 
generating lottery numbers, commenting on pages, a fruit machine, and more - 
all of which was pretty unheard of in those days when the world wide web was 
in its infancy in academia.

This demo application is a rewrite of the Anonymous Message Server, albeit 
without the complete disregard for security 30 something years ago! You visit
the page, and are shown a message left by the most recent previous visitor. You
can then leave a message for the next user, and view all the past messages.

Obviously this is a completely useless application, and would (unfortunately) 
probably be abused to within an inch of its life in this day and age, so **DO
NOT DEPLOY IT ON THE INTERNET!** In the 90's though, people were much less
likely to do nasty things to poorly designed websites.

## Application

The application itself is a pretty standard, basic Django project. It 
implements a single Django application with a couple of template-driven views.

The magic that this application is intended to illustrate is the database query
routing. In a Django application, the settings module allows you to specify one
or more database connections. Often, users will just set the 'default' 
database to point to the one database they're using for their application, for
example;

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydb',
        'USER': 'myuser',
        'PASSWORD': 'secret',
        'HOST': '192.168.107.43',
        'PORT': 5432
    }
}
```

However, we can define additional databases as well:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'coredb',
        'USER': 'myuser',
        'PASSWORD': 'secret',
        'HOST': '192.168.107.43',
        'PORT': 5432
    },
    'accounts': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'accountsdb',
        'USER': 'myuser',
        'PASSWORD': 'secret',
        'HOST': '192.168.155.76',
        'PORT': 5432
    }
}
```

In the most simple case, we might tell Django what database to use whenever we
want to access anything except the default one. Typically this will involve
using the *using* method of a model object:

```python
Transaction.objects.using('accounts').all()
```

Would return all the *Transaction* records from the *accounts* database. In 
other cases, the *using* keyword argument might be used:

```python
transaction.save(using='accounts')
```

This will save a *transaction* object to the *accounts* database.

However, this basic method of routing database queries can be tedious to 
implement in large applications, and arguably lends itself more to application
based sharding than the load balancing that this application is intended to 
illustrate.

## Load Balancing using Database Routing

Django allows us to create database router classes that can be chained together 
to find the correct database connection to use for any given operation. If no 
suitable database is found, the *default* connection is used.

Before we dive into that, recall that in this example the point is to 
demonstrate how to load balance across a PostgreSQL cluster that consists of a
primary server and one or more read-only standby servers. It is assumed that
[PgBouncer](https://www.pgbouncer.org) is used to load balance across multiple
standby servers: whilst the application could be written to support multiple 
read-only servers directly, it's easier to use PgBouncer as that allows us to
reconfigure and resize the cluster as needed, with changes required to the 
PgBouncer configuration only. In fact, it makes sense to route the read-write
connection through PgBouncer as well, as it's trivial to reconfigure to point
to a new server in the event of a failover or switchover.

We need to do three things to implement a database router:

1) Define the database connections. both the *primary* and *standby* databases
   will point to PgBouncer, with the *primary* being a pool over the primary
   server in the cluster, and the *standby* being a pool over all the standby
   servers in the cluster:
   
   ```python
   DATABASES = {
       'default': {},
       'primary': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'msgsvr_rw',
           'USER': 'msgsvr',
           'PASSWORD': 'secret',
           'HOST': '/tmp',
           'PORT': '6432',
       },
       'standby': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'msgsvr_ro',
           'USER': 'msgsvr',
           'PASSWORD': 'secret',
           'HOST': '/tmp',
           'PORT': '6432',
       }
    }   
   ```

1) Next, we create our router class. This implements four methods that we can
   add whatever logic we want to. These methods have access to the model, 
   objects or other information that will help us decide where to route any 
   given database operation:
   
   ```python
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
   ```
   
1) We need to register our router in the *settings* module for the project:
    
   ```bash
   DATABASE_ROUTERS = ['website.db_router.DbRouter']
   ```
   
In a more complex design, we might include multiple routers in the list, which 
will be called in the order that they are listed, until a database name is 
returned. If none of the routers return a database name (i.e. they all return 
*None*), then the *default* database will be used.

## Final Thoughts

Creating a database router in Django can be extremely simple, or complex if 
your needs require it. They can allow simple routing based on whether or not
an operation requires read or write access to the database, which when used with
PgBouncer over a PostgreSQL streaming replication cluster can offer a powerful
way to load balance and scale an application that is primarily read intensive
(as most are). This pattern allows us to easily reconfigure and scale the
cluster without the need to make application changes.

More complex designs can be used to distribute data for different applications
within the Django project, or even to store different models on different 
databases.