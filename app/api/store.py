from flask import Blueprint, request, jsonify, current_app
import requests
from app.api.auth import token_required
from app.services.store_service import StoreService
from app.services.shopify_oauth_service import ShopifyOAuthService

store_bp = Blueprint('store', __name__)

@store_bp.route('/stores/connect', methods=['POST'])
@token_required
def connect_store(current_user):
    """Initiate Shopify store connection"""
    data = request.get_json()
    
    if 'store_url' not in data:
        return jsonify({'message': 'Missing store URL'}), 400
    
    # Generate authorization URL with user_id
    auth_url = ShopifyOAuthService.generate_authorization_url(
        data['store_url'],
        current_user.id
    )
    return jsonify({'auth_url': auth_url}), 200

@store_bp.route('/oauth/callback', methods=['GET'])
def oauth_callback():
    """Handle Shopify OAuth callback"""
    # Get parameters from request
    shop = request.args.get('shop')
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not all([shop, code, state]):
        return jsonify({'message': 'Missing required parameters'}), 400
    
    # Complete OAuth flow
    oauth_result = ShopifyOAuthService.complete_oauth_flow(shop, code, state)
    
    if not oauth_result['success']:
        return jsonify({'message': oauth_result['message']}), 400
    
    # Add store to database
    store_data = oauth_result['data']
    success, message, store = StoreService.add_store(
        user_id=store_data['user_id'],
        store_url=store_data['shop'],
        access_token=store_data['access_token'],
        store_name=store_data['shop_name']
    )
    
    if not success:
        return jsonify({'message': message}), 400
    
    return jsonify({
        'message': 'Store connected successfully',
        'data': store
    }), 200

@store_bp.route('/stores', methods=['POST'])
@token_required
def add_store(current_user):
    """Add a new Shopify store"""
    data = request.get_json()
    
    if not all(k in data for k in ['store_url', 'access_token']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Verify the access token with Shopify
    if not StoreService.verify_shopify_token(data['store_url'], data['access_token']):
        return jsonify({'message': 'Invalid Shopify access token'}), 400

    success, message, store_data = StoreService.add_store(
        user_id=current_user.id,
        store_url=data['store_url'],
        access_token=data['access_token'],
        store_name=data.get('store_name')
    )
    
    if success:
        return jsonify({'message': message, 'data': store_data}), 201
    return jsonify({'message': message}), 400

@store_bp.route('/stores', methods=['GET'])
@token_required
def get_stores(current_user):
    """Get all stores for the current user"""
    stores = StoreService.get_user_stores(current_user.id)
    return jsonify({'stores': stores}), 200

@store_bp.route('/stores/<int:store_id>', methods=['PUT'])
@token_required
def update_store(current_user, store_id):
    """Update store details"""
    data = request.get_json()
    
    if 'store_name' not in data:
        return jsonify({'message': 'Missing store name'}), 400
    
    success, message, store_data = StoreService.update_store(
        user_id=current_user.id,
        store_id=store_id,
        store_name=data['store_name']
    )
    
    if success:
        return jsonify({'message': message, 'data': store_data}), 200
    return jsonify({'message': message}), 400

@store_bp.route('/stores/<int:store_id>', methods=['DELETE'])
@token_required
def delete_store(current_user, store_id):
    """Delete a store"""
    success, message = StoreService.delete_store(
        user_id=current_user.id,
        store_id=store_id
    )
    
    if success:
        return jsonify({'message': message}), 200
    return jsonify({'message': message}), 400

@store_bp.route('/stores/<int:store_id>', methods=['GET'])
@token_required
def get_store(current_user, store_id):
    """Get a single store by ID"""
    store = StoreService.get_store_by_id(store_id)
    if not store:
        return jsonify({'message': 'Store not found'}), 404
    
    # Check if store belongs to user
    if store.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    return jsonify({'data': store.to_dict()}), 200 