# myHouse2eGeoffrey Migration Utilities

These utilities help in migrating from myHouse (https://github.com/myhouse-project) to eGeoffrey (https://www.egeoffrey.com).
The following two scripts are provided:

- `migrate_config.py`: which convert myHouse's `config.json` file in eGoeffrey configuration files
- `migrate_dabase.py`: which convert myHouse's redis database into an eGoeffrey redis database

Despite the scrips automate a lot of tasks, there is not always a one-to-one match between myHouse's configuration settings and eGoeffrey's. For this reason, whenever an automatic conversion would not be possible, a message with instructions on how to proceed manually is provided by the script.

## Migrate the configuration

The script convert a myHouse v2.4 configuration file into an eGeoffrey format. Place your `config.json` file into the directory where this script resides and just run it. The new configuration will be created into a `config` directory which can be directly used in eGeoffrey.

## Migrate the database

The script convert a myHouse v2.4 database into the eGeoffrey format. Place your `config.json` file into the directory where this script resides and just run it. The script will connect to the database and migrate every key in the next database number (e.g. if myHouse database was in database number 1, eGeoffrey's database will be created in database number 2).


