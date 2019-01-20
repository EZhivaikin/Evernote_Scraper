# import hashlib
# import binascii

import codecs
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.type.ttypes as Types
from evernote.edam.notestore import NoteStore
from evernote.api.client import EvernoteClient
import subprocess
import Enex_parser
import xml.etree.ElementTree as ET
import os
# Real applications authenticate with Evernote using OAuth, but for the
# purpose of exploring the API, you can get a developer token that allows
# you to access your own Evernote account. To get a developer token, visit
# https://SERVICE_HOST/api/DeveloperToken.action
#
# There are three Evernote services:
#
# Sandbox: https://sandbox.evernote.com/
# Production (International): https://www.evernote.com/
# Production (China): https://app.yinxiang.com/
#
# For more information about Sandbox and Evernote China services, please
# refer to https://dev.evernote.com/doc/articles/testing.php
# and https://dev.evernote.com/doc/articles/bootstrap.php

MD_PATH = 'content/'
MEDIA_PATH = 'output/media/'
auth_token = "S=s1:U=951f6:E=16fae2c3750:C=168567b0790:P=1cd:A=en-devtoken:V=2:H=b39ee5524adaec7eb02757027b1dea10"
# To access Sandbox service, set sandbox to True
# To access production (International) service, set both sandbox and china to False
# To access production (China) service, set sandbox to False and china to True
sandbox = True
china = False

# Initial development is performed on our sandbox server. To use the production
# service, change sandbox=False and replace your
# developer token above with a token from
# https://www.evernote.com/api/DeveloperToken.action
client = EvernoteClient(token=auth_token, sandbox=sandbox, china=china)

user_store = client.get_user_store()

version_ok = user_store.checkVersion(
    "Evernote EDAMTest (Python)",
    UserStoreConstants.EDAM_VERSION_MAJOR,
    UserStoreConstants.EDAM_VERSION_MINOR
)
print("Is my Evernote API version up to date? ", str(version_ok))
print("")
if not version_ok:
    exit(1)

note_store = client.get_note_store()

notebooks = note_store.listNotebooks()
print("Found ", len(notebooks), " notebooks:")
for notebook in notebooks:
    print("  * ", notebook.guid)
    filter = NoteStore.NoteFilter()
    filter.ascending = False
    filter.notebookGuid = notebook.guid

    spec = NoteStore.NotesMetadataResultSpec()
    spec.includeTitle = True
    spec.includeNotebookGuid = True
    spec.includeTagGuids = True
    # Запрос всех заметок.
    ourNoteList = note_store.findNotesMetadata(filter, 0, 25, spec)
    for note in ourNoteList.notes:
        # Получение метаданных заметок.
        note_data = note_store.getNote(note.guid, True, True, True, False)
        print(note_data.title)
        filename = MD_PATH + note_data.title + ".enex"
        # Сохранение enex-файла и его парсинг в md.
        if not os.path.exists(MD_PATH+note_data.title):
            os.mkdir(MEDIA_PATH+"/"+note_data.title)
            with open(filename, 'w',  encoding='UTF-8') as fw:
                fw.write(
                    "<note><title>%s</title><content><![CDATA[" % note_data.title)
                fw.write(str(note_data.content))
                fw.write("]]></content></note>")
            Enex_parser.evernote_dump.run_parse([filename], path=MD_PATH)
        # Сохранение прикрепленных к заметке файлов.
            if not note_data.resources is None:
                for resource in note_data.resources:
                    if not resource.recognition is None:
                        # Получаем их ID в разметке чтобы позже привязать к md.
                        objID = ET.fromstring(
                            resource.recognition.body).get('objID')
                        # Дописать в конец файла ссылки на файлы в md
                        with open(MD_PATH+"%s/%s.md" % (note_data.title, note_data.title), 'a') as fw:
                            # Заменяем пробелы на %20 т.к. иначе путь не считывается
                            fw.write("\n\n[%s]:\n/%s/%s" % (objID, MEDIA_PATH +
                                                            note_data.title.replace(' ', '%20'), resource.attributes.fileName.replace(' ', '%20')))
                    with open("%s/%s" % (MEDIA_PATH+note_data.title, resource.attributes.fileName), 'wb') as handler:
                        handler.write(resource.data.body)
