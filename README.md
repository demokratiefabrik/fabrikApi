# fabrikApi Python-Pyramid-Server

The REST-Api 'fabrikApi' is a collection of peer-production-plugins made for civic-tech applications. A key feature is the self-governance logic, by which main user acitivities have to be reviewed by randomly sampled peers. ( Review-by-random-peers; RbRP).

The plugins are still to be implemented. Including:
- VAA-questionnaire peer-production. 
- content tree peer-production (for Citizen Initiative Review).


## Plugins
It will be possible to extend the platform with own developped peer-production plugins.
1) Save the pluging under fabrikApi.plugins
2) Initalize the plugin in the fabrikApi.\_\_init\_\_.py 
> config.include('.plugins.container', route_prefix='/tree') 
3) Extend also the PluginMixins Inheritances fabrikApi.plugins.meta. This allows to attach the plugins to the core assembly table and to use the core user-tracking table also for pluging activites. 
> class PluginMixins (ContainerMixin, YourPlugins):\
> &nbsp;&nbsp;&nbsp;&nbsp;pass


## Authorization / Authentication
XHR-Requests on resources require an JWT Authorization header. The JWT token is created by fabrikAuth-oAuth2-Provider.

The Api perfectly collaborates with the fabrikAuth oAuth-Provider. Third-party oAuth Servers can be implemented, theoretically.

Authorization is organized by roles attached to assemblies.\

* Roles:\
  - UNAUTHENTICATED: This are unautheniticated visitors.
  - AUTHENTICATED: read-only guests. (Typically, this are the self-authenticated users.)
  - CONTRIBUTORS: Users have the permission to add proposals, raise questions or answering them. 
  - MODERATOR: Moderators have the permission to take moderation decisions. (Typically, for random-sampled citizen assemblies, this is the role of the sampled citizens.\
  - MANAGER: Only "Administrators" can manage Assemblies (edit name, start date, end-date etc.). This is the role of event organizers.
  - ADMINISTRATOR: While administrator-roles are  attached to an assembly: The "Super-Administrator" is a global role. i.e. They  can add or delete assemblies. This is the event of the server managers.

Hence, persmission can be granted by adding JWT scopes: "<role>@<assembly_identifier>". A user that shall have Moderator-permission in the assembly digikon2022 shall obtain the role "moderator@digikon2022"



## SETUP

> $VENV/bin/pip install -e .

> $VENV/bin/initialize_fabrikApi_db development.ini

> python setup.py develop


Start developping server...
> $VENV/bin/pserve development.ini --reload

## setup PROD

# DOCKER

## Builds
Autobuild is enabled. After each git/push a new docker build is generated.
For manually builds, you may enter:

> docker build -f Dockerfile -t demokratiefabrik/fabrikapi .
> docker push demokratiefabrik/fabrikapi:latest
(or push it via portainer)

## Runs
> docker run --publish 8020:8020 --link fabrikdb --detach --name fabrikApi demokratiefabrik/fabrikapi:latest

# RUN PORTAINER
sudo docker volume create portainer_data

sudo docker run -d -p 8001:8000 -p 9000:9000 --name=portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer