from flask_restx import Namespace, Resource, fields, reqparse
from flask import request
from api import token_required, limiter, cache
from data_loader import JSONDataLoader
from logger_config import get_logger

logger = get_logger(__name__)

ns = Namespace('properties', description='Operaciones sobre las propiedades scrapeadas')

property_model = ns.model('Property', {
    'id': fields.String(description='Identifier of the property'),
    'titulo': fields.String(description='Property title'),
    'precio': fields.String(description='Property string price'),
    'operacion': fields.String(description='Operacion type'),
    'tipo': fields.String(description='Property type'),
    'ubicacion': fields.String(description='Property location'),
    'url': fields.String(description='Property URL')
})

# Setup parser for standard property search
parser = reqparse.RequestParser()
parser.add_argument('operacion', type=str, help='Tipo de operación')
parser.add_argument('tipo', type=str, help='Tipo de propiedad')
parser.add_argument('precio_min', type=float, help='Precio Mínimo (CLP)')
parser.add_argument('precio_max', type=float, help='Precio Máximo (CLP)')
parser.add_argument('search', type=str, help='Búsqueda basada en texto de título/ubicación')
parser.add_argument('page', type=int, default=1, help='Número de página actual')
parser.add_argument('per_page', type=int, default=20, help='Items por página')

@ns.route('')
class PropertyList(Resource):
    @ns.doc('list_properties', security='apikey')
    @ns.expect(parser)
    @token_required
    @limiter.limit("60 per minute")
    @cache.cached(timeout=60, query_string=True)
    def get(self):
        """Lista todas las propiedades con paginación y filtros"""
        try:
            loader = JSONDataLoader()
            args = parser.parse_args()
            file_param = request.args.get('file')

            if file_param:
                properties = loader.load_specific_json_file(file_param)
            else:
                latest_file = loader.get_latest_json_file()
                if latest_file:
                    properties = loader.load_specific_json_file(latest_file['filename'])
                else:
                    properties = loader.load_all_json_files()

            filters = {
                'operacion': args.get('operacion'),
                'tipo': args.get('tipo'),
                'precio_min': args.get('precio_min'),
                'precio_max': args.get('precio_max'),
                'search': args.get('search')
            }
            filters = {k: v for k, v in filters.items() if v is not None}

            if filters:
                filtered_probs = []
                for prop in properties:
                    if filters.get('operacion') and prop.get('operacion') != filters['operacion']:
                        continue
                    if filters.get('tipo') and prop.get('tipo') != filters['tipo']:
                        continue
                    
                    precio_clp = loader._extract_price_clp(prop.get('precio', ''))
                    if filters.get('precio_min') is not None and (precio_clp is None or precio_clp < filters['precio_min']):
                        continue
                    if filters.get('precio_max') is not None and (precio_clp is None or precio_clp > filters['precio_max']):
                        continue
                        
                    if filters.get('search'):
                        search_lower = filters['search'].lower()
                        titulo = prop.get('titulo', '').lower()
                        ubicacion = prop.get('ubicacion', '').lower()
                        if search_lower not in titulo and search_lower not in ubicacion:
                            continue
                    
                    filtered_probs.append(prop)
                properties = filtered_probs

            page = args.get('page')
            per_page = args.get('per_page')
            paginated = loader.paginate(properties, page, per_page)
            
            return {
                'success': True,
                'data': paginated['data'],
                'pagination': {
                    'page': paginated['page'],
                    'per_page': paginated['per_page'],
                    'total': paginated['total'],
                    'pages': paginated['total_pages']
                }
            }
        except Exception as e:
            logger.error(f"Error fetching properties: {e}")
            ns.abort(500, str(e))

@ns.route('/<string:property_id>')
@ns.response(404, 'Property not found')
@ns.param('property_id', 'The property identifier')
class PropertyDetail(Resource):
    @ns.doc('get_property', security='apikey')
    @token_required
    @limiter.limit("120 per minute")
    @cache.cached(timeout=300)
    def get(self, property_id):
        """Devuelve el detalle completo de una propiedad"""
        try:
            loader = JSONDataLoader()
            properties = loader.load_all_json_files()
            prop = next((p for p in properties if p.get('id') == property_id), None)
            
            if not prop:
                ns.abort(404, "Property not found")
                
            return {
                'success': True,
                'data': prop
            }
        except Exception as e:
            logger.error(f"Error fetching property detail: {e}")
            ns.abort(500, str(e))
