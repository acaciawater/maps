from django.core.management.base import BaseCommand
from maps.models import Document
from sorl.thumbnail.shortcuts import get_thumbnail

import logging
from sorl.thumbnail import default
from sorl.thumbnail.helpers import get_module_class
logger = logging.getLogger(__name__)

IMAGEMAGICK_ENGINE='sorl.thumbnail.engines.convert_engine.Engine'
PIL_ENGINE='sorl.thumbnail.engines.pil_engine.Engine'

class Command(BaseCommand):

    help = 'Create or update thumbnails'
    
    def add_arguments(self, parser):
        parser.add_argument('geom',help='sorl geometry')
        parser.add_argument('--doc','-d', help='document')
        
    def handle(self, *args, **options):
        geom = options.get('geom')
        pk = options.get('doc')
        docs = Document.objects.all()
        pil = get_module_class(PIL_ENGINE)()
        pdf = get_module_class(IMAGEMAGICK_ENGINE)()
        if pk:
            docs = docs.filter(pk=pk)
        for doc in docs:
            if doc.doc:
                engine = pdf if doc.doc.name.lower().endswith('pdf') else pil
                logger.info('Processing document %s with engine %s', doc, engine)
                default.engine = engine
                im=get_thumbnail(doc.doc, geom)
                if im is None:
                    logger.error('failed')