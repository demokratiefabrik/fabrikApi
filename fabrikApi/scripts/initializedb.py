import csv
import os
import sys

import transaction
from pyramid import testing
from pyramid.paster import get_appsettings, setup_logging
from pyramid.scripts.common import parse_vars

from fabrikApi.models import DBAssembly, DBContentTree, DBContent, DBUser, \
    get_engine, get_session_factory, get_tm_session
from fabrikApi.models.meta import Base
from fabrikApi.models.stage import DBStage
from datetime import timedelta
import arrow


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [var=value]\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    options = parse_vars(argv[2:])
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, options=options)

    engine = get_engine(settings)

    # DELTE ALL TABLES
    Base.metadata.drop_all(engine)
    # ADD NEW TABLE
    Base.metadata.create_all(engine)

    session_factory = get_session_factory(engine)

    with transaction.manager:
        dbsession = get_tm_session(session_factory, transaction.manager)

        request = testing.DummyRequest()
        # request.settings = {}
        # request.settings["MAX_ALLOWED_LEVELS_IN_application"] = 10
        request.dbsession = dbsession

        if settings["example_data"] == "true":

            # ADD CONTENT        
            setup_data(request)

            # COmmit
            transaction.commit()
            print("---------------------")
            print("DATA SETUP FINALIZED")
            print("---------------------")


        print("---------------------")
        print("DONE")
        print("---------------------")


def setup_data(request):

    dbsession = request.dbsession

    # generate one admin user
    print("###################################")
    print("GENERAL DATA: ")
    print("--- Users --- ")
    user_1 = DBUser(
        oauth2_provider=u"LOCAL",
        oauth2_user_id=1,
        username="localadmin")

    dbsession.add(user_1)

    print("--- Assemblies --- ")

    print("ASSEMBLY 1: ")
    info = """Am 31. Juni findet die Abstimmung über die Initiative XY statt. Wir haben 1000
    Einwohner der Schweiz eingeladen, zusammen eine Entscheidungshilfe zu erarbeiten. Die
    Entscheidungsgrundlage wird dann rechtzeitig der Öffentlichkeit zur Verfügung
    gestellt. Sie hilft den StimmbürgerInnen einen fairen und versierten Stimmentscheid zu fällen."""
    assembly1 = DBAssembly(title='Volksinitiative XY',
        caption='Eine BürgerInnenversammlung zur Erstellung einer öffentlichen Entscheidungsgrundlage für die nationale Abstimmung über die Vorlage XYZ',
        identifier='initiativeXY',
        info=info,
        image="/upload/citizenassembly.png")
    
    # future date
    dt = arrow.utcnow()
    td = timedelta(weeks=3)
    assembly1.date_end = dt + td

    dbsession.add(assembly1)
    dbsession.flush()
    # TODO: auto sync permissions in fabrikAuth

    print("A1 - PLUGINS: ")

    print("--- INTRODUCTION --- ")
    c11 = import_tree(
        request=request,
        file="CIR_TEXTSHEET_INTRODUCTION",
        assembly=assembly1,
        info = "Sie finden hier alle Informationen rund um diesen Event. Schauen Sie sich diese Informationen an. Sie haben auch sptäter noch jederzeit Gelegenheit hierher zurückzukehren.",
        title="Was Sie wissen müssen",
        user=user_1,
        reordering=True,
        type_="TEXTSHEET")

    c12 = import_tree(
        request=request,
        file="CIR",
        title="Wichtigste Pro- und Kontraargumente",
        info=("Wir brauchen hier Ihre Mithilfe! Was spricht für die Vorlage und was dagegen. "
             "Welches sind die wirklich relevanten Inhalte?"),
        assembly=assembly1,
        user=user_1,
        type_="PROS_AND_CONS")

    # ADD STAGES
    print("A1 - STAGES: ")

    ## CREATE STAGES FOR ASSEMBLY 2
    stage1 = DBStage(
        title="Was Sie wissen müssen",
        info = "Sie finden hier alle Informationen rund um diesen Event. Schauen Sie sich diese Informationen an. Sie haben auch sptäter noch jederzeit Gelegenheit hierher zurückzukehren.",
        assembly=assembly1,
        type_='TEXTSHEET',
        contenttree=c11)
    dbsession.add(stage1)

    stage2 = DBStage(
        title="Befragung",
        info="Bevor wir starten, möchten wir Sie bitten einen kurzen Fragebogen über Sie auszufüllen. Sämtliche Angaben werden für die wissenschaftiche Begleitstudie in anonymisierter Form ausgewertet. Andere Verwendungszwecke sind ausgeschlossen.",
        type_='SURVEY',
        custom_data={"provider": "qualtrics", "SID": "SV_d73INEkbZ3cUN7v"},
        assembly=assembly1)
    dbsession.add(stage2)

    stage3 = DBStage(
        title="Die wichtigsten politischen Themen",
        type_='CIR',
        info="Nun geht es los. In diesem Abschnitt geht es darum, die wichtigsten Argumente für oder gegen die Vorlage zu sammeln.",
        assembly=assembly1,
        contenttree=c12)
    dbsession.add(stage3)

    stage5 = DBStage(
        title="Erste Resultate",
        type_='CIR_ANALYSIS',
        info="Hier stellen wir Ihnen erste, provisorische Resultate zusammen. Was ist den Teilnehmenden Stimmbürgern für die nächste Legislatur besonders wichtig?",
        assembly=assembly1,
        contenttree=c12)

    dbsession.add(stage5)

    print("ASSEMBLY 2: ")
    info = """Am 31. November finden die kantonalen Wahlen in XZ statt. Wir haben 1000
    zufällig ausgewählte Einwohner des Kantons eingeladen, zusammen eine öffenltiche
    Wahlhilfe zu erarbeiten. Die Wahlhilfe wird dann rechtzeitig der Öffentlichkeit zur Verfügung
    gestellt. Sie hilft den StimmbürgerInnen dabei aus den zahlreichen Kandididierenden, diejenigen
    zu finden, welche mit den persönlichen politischen Vorstellungen am meisten übereinstimmen."""
    assembly2 = DBAssembly(title='Parlamentswahl in XY', 
        caption='Eine BürgerInnenversammlung zur Zusammestellung eines Smartvote-Fragebogens für die Könizer Parlamentswahlen', 
        identifier='digikon2022', 
        info=info,
    image="/upload/keisel.jpg")
    dbsession.add(assembly2)
    dbsession.flush()

    print("A2 - CONTAINERS: ")
    c21 = import_tree(
        request=request,
        user=user_1,
        title="INTRODUCTION",
        file="VAA_TEXTSHEET_INTRODUCTION",
        assembly=assembly2,
        type_="TEXTSHEET"
    )
    
    c22 = import_tree(
        request=request,
        file="VAA_CONTENT",
        title="VAA-QUESTIONNAIRE",
        assembly=assembly2,
        type_="VAA",
        user=user_1,
        reordering=True
    )

    # ADD STAGES
    print("A2 - STAGES: ")
    ## CREATE STAGES FOR ASSEMBLY 2
    stage1 = DBStage(
        title="Was Sie wissen müssen",
        info = "Sie finden hier alle Informationen rund um diesen Event. Schauen Sie sich diese Informationen an. Sie haben auch sptäter noch jederzeit Gelegenheit hierher zurückzukehren.",
        assembly=assembly2,
        type_="TEXTSHEET",
        contenttree = c21)
    dbsession.add(stage1)

    stage2 = DBStage(
        title="Befragung",
        info = "Bevor wir starten, möchten wir Sie bitten einen kurzen Fragebogen über Sie auszufüllen. Sämtliche Angaben werden für die wissenschaftiche Begleitstudie in anonymisierter Form ausgewertet. Andere Verwendungszwecke sind ausgeschlossen.",
        type_='SURVEY',
        custom_data={"provider": "qualtrics", "SID": "SV_d73INEkbZ3cUN7v"},
        assembly=assembly2)
    dbsession.add(stage2)

    stage3 = DBStage(
        title = "Die wichtigsten politischen Themen",
        type_='VAA_TOPICS',
        info = "Nun geht es los. In diesem Abschnitt geht es darum, die wichtigsten politischen Themen der nächsten Legislatur zu identifizieren. Welche politischen Herausforderungen liegen Ihnen besonders am Herzen?",
        assembly=assembly2,
        contenttree = c22)
    dbsession.add(stage3)

    stage4 = DBStage(
        title = "Der Fragebgen",
        type_='VAA_QUESTIONS',
        info = "Nun wird es konkret: Bei welchen Sachfragen müssen die Kandidaten mit Ihnen übereinstimmen, damit Sie sie wählen würden.",
        assembly=assembly2,
        contenttree = c22)
    dbsession.add(stage4)

    stage5 = DBStage(
        title = "Erste Resultate",
        type_='VAA_CONCLUSION',
        info ="Hier stellen wir Ihnen erste, provisorische Resultate zusammen. Was ist den Teilnehmenden Stimmbürgern für die nächste Legislatur besonders wichtig.",
        assembly=assembly2,
        contenttree=c22)

    dbsession.add(stage5)
    dbsession.flush()


def import_tree(request, argv=sys.argv, lock_topic_after=0, assembly=None, user=None,
        file=None, title=None, type_=None, info=None, reordering=False):

    # import example data (e.g. Swiss expulsion initiative (deliberatorium
    # export)
    contenttree1 = DBContentTree(title=title, type_=type_, assembly=assembly)
    request.dbsession.add(contenttree1)
    request.dbsession.flush()

    contenttree_id = contenttree1.id
    assert contenttree1.id

    with open('./fabrikApi/scripts/dump/%s.csv' % file, 'r') as csvfile:
        # DictReader
        # with open(f, newline='\n') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        # reader = csv.DictReader(csvfile)
        # # csvreader = csv.reader(csvfile, delimiter=';', quotechar='"')
        parent_translation = [0]
        arg = None
        i = 0

        id_translation = {}
        parents = []
        contents = {}

        # for row in csvreader:
        for row in reader:
            row = dict(row)
            # print(row)
            title = row['title']
            type_ = row['type']
            text = row['text']
            parent = row['parent_id']
            id_ = row['id']
            # level = row['full_branch'].count('-')
            textsplit = text.split("$text")
            if len(textsplit) > 1:
                text = textsplit[1]
            if len(title) >= 50:
                title = "TEST"
            parent_id = None
            # if parent:

            if parent:
                parent_id = id_translation[int(parent)]
            arg = DBContent(
                text=text,
                title=title,
                type_=type_,
                parent_id=parent_id,
                contenttree_id=contenttree_id,
                user_id=user.id)
            request.dbsession.add(arg)
            parent_translation.append(arg.id)
            request.dbsession.flush()
            id_translation[int(id_)] = arg.id
            arg.patch()
            
            request.dbsession.flush()

            contents[arg.id] = arg
            if arg.parent_id and arg.parent_id not in parents:
                parents.append(arg.parent_id)
        
        # Reordering all children of this tree.
        if reordering:
            for parent_id in parents:
                if contents[parent_id]:
                    if contents[parent_id].db_ordered_children:
                        contents[parent_id].db_ordered_children.reorder()


    assert user.id
    assert contenttree1.id

    contenttree1.db_ordered_children.reorder()
    return (contenttree1)
