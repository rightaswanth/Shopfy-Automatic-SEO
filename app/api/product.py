from flask import Blueprint, request, jsonify
from app.api.auth import token_required
from app.services.product_service import ProductService
from app.services.gemini_service import GeminiService

product_bp = Blueprint('product', __name__)

@product_bp.route('/stores/<int:store_id>/products/sync', methods=['POST'])
@token_required
def sync_products(current_user, store_id):
    """Sync products from Shopify store"""
    success, message, data = ProductService.fetch_products_from_shopify(store_id)
    
    if success:
        return jsonify({
            'message': message,
            'data': data
        }), 200
    return jsonify({'message': message}), 400

@product_bp.route('/stores/<int:store_id>/products', methods=['GET'])
@token_required
def get_store_products(current_user, store_id):
    """Get all products for a store with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    products, total, pages = ProductService.get_store_products(
        store_id=store_id,
        page=page,
        per_page=per_page
    )
    
    return jsonify({
        'products': products,
        'total': total,
        'pages': pages,
        'current_page': page
    }), 200

@product_bp.route('/products/<int:product_id>', methods=['GET'])
@token_required
def get_product(current_user, product_id):
    """Get a specific product with its optimized descriptions"""
    product = ProductService.get_product_by_id(product_id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404
    
    # Get optimized descriptions
    descriptions = ProductService.get_product_optimized_descriptions(product_id)
    product['optimized_descriptions'] = descriptions
    
    return jsonify({'data': product}), 200

@product_bp.route('/products/<int:product_id>/optimize', methods=['POST'])
@token_required
def optimize_product(current_user, product_id):
    """Generate SEO-optimized description for a product"""
    data = request.get_json()
    keywords = data.get('keywords', [])
    
    # Generate optimized description
    success, message, description_data = GeminiService.generate_seo_description(
        product_id=product_id,
        keywords=keywords
    )
    
    if not success:
        return jsonify({'message': message}), 400
    
    # Save the optimized description
    success, message, saved_description = ProductService.create_optimized_description(
        product_id=product_id,
        optimized_description=description_data['optimized_description']
    )
    
    if success:
        return jsonify({
            'message': 'Description generated and saved successfully',
            'data': saved_description
        }), 201
    return jsonify({'message': message}), 400

@product_bp.route('/products/bulk-optimize', methods=['POST'])
@token_required
def bulk_optimize_products(current_user):
    """Generate SEO-optimized descriptions for multiple products"""
    data = request.get_json()
    
    if 'product_ids' not in data:
        return jsonify({'message': 'Missing product IDs'}), 400
    
    # Format keywords as a dictionary with product IDs as keys
    keywords_dict = {}
    if 'keywords' in data:
        for product_id in data['product_ids']:
            keywords_dict[product_id] = data['keywords']
    
    # Generate optimized descriptions
    success, message, descriptions = GeminiService.generate_bulk_seo_descriptions(
        product_ids=data['product_ids'],
        keywords=keywords_dict
    )
    
    if not success:
        return jsonify({'message': message}), 400
    
    # Save all generated descriptions
    saved_descriptions = []
    for desc in descriptions:
        if 'error' not in desc:
            success, _, saved_desc = ProductService.create_optimized_description(
                product_id=desc['product_id'],
                optimized_description=desc['optimized_description']
            )
            if success:
                saved_descriptions.append(saved_desc)
    
    return jsonify({
        'message': f'Generated and saved {len(saved_descriptions)} descriptions',
        'data': saved_descriptions
    }), 201

@product_bp.route('/descriptions/<int:description_id>', methods=['PUT'])
@token_required
def update_description(current_user, description_id):
    """Update an optimized description"""
    data = request.get_json()
    
    if 'optimized_description' not in data:
        return jsonify({'message': 'Missing optimized description'}), 400
    
    success, message, description = ProductService.update_optimized_description(
        description_id=description_id,
        optimized_description=data['optimized_description']
    )
    
    if success:
        return jsonify({
            'message': message,
            'data': description
        }), 200
    return jsonify({'message': message}), 400

@product_bp.route('/descriptions/<int:description_id>/deploy', methods=['POST'])
@token_required
def deploy_description(current_user, description_id):
    """Deploy an optimized description to Shopify"""
    success, message, _ = ProductService.deploy_optimized_description(description_id)
    
    if success:
        return jsonify({'message': message}), 200
    return jsonify({'message': message}), 400

@product_bp.route('/descriptions/<int:description_id>', methods=['DELETE'])
@token_required
def delete_description(current_user, description_id):
    """Delete an optimized description"""
    success, message = ProductService.delete_optimized_description(description_id)
    
    if success:
        return jsonify({'message': message}), 200
    return jsonify({'message': message}), 400 