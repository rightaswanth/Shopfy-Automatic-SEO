import hmac
import hashlib
import requests
import json
from urllib.parse import urlencode
from flask import current_app
from app.services.store_service import StoreService
from app import redis_obj

class ShopifyOAuthService:
    @staticmethod
    def generate_authorization_url(shop_url: str, user_id: int, scopes: list = None) -> str:
        """
        Generate the authorization URL for Shopify OAuth
        """
        # Normalize shop URL
        if not shop_url.endswith('.myshopify.com'):
            shop_url = f"{shop_url}.myshopify.com"
        
        # Default scopes if none provided
        if scopes is None:
            scopes = [
                'read_products',
                'write_products',
                'read_orders',
                'write_orders',
                'read_customers',
                'write_customers',
                'read_inventory',
                'write_inventory',
                'read_fulfillments',
                'write_fulfillments',
                'read_shipping',
                'write_shipping',
                'read_analytics',
                'read_merchant_managed_fulfillment_orders',
                'write_merchant_managed_fulfillment_orders',
                'read_third_party_fulfillment_orders',
                'write_third_party_fulfillment_orders'
            ]
        
        # Generate state parameter for security
        state = hmac.new(
            current_app.config['SHOPIFY_API_SECRET'].encode('utf-8'),
            shop_url.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Store state and user_id in Redis with 1-hour expiry
        redis_obj.setex(
            f"shopify_oauth_state:{state}",
            3600,  # 1 hour expiry
            json.dumps({
                'user_id': user_id,
                'shop_url': shop_url
            })
        )
        
        # Build authorization URL
        params = {
            'client_id': current_app.config['SHOPIFY_API_KEY'],
            'scope': ','.join(scopes),
            'redirect_uri': f"{current_app.config['SHOPIFY_APP_URL']}/v1/store/oauth/callback",
            'state': state
        }
        
        return f"https://{shop_url}/admin/oauth/authorize?{urlencode(params)}"
    
    @staticmethod
    def verify_state(state: str) -> tuple:
        """
        Verify the state parameter and return stored data
        """
        stored_data = redis_obj.get(f"shopify_oauth_state:{state}")
        if not stored_data:
            return False, None, None
            
        data = json.loads(stored_data)
        return True, data.get('user_id'), data.get('shop_url')
    
    @staticmethod
    def clear_state(state: str):
        """
        Clear the stored state from Redis
        """
        redis_obj.delete(f"shopify_oauth_state:{state}")
    
    @staticmethod
    def exchange_code_for_token(shop: str, code: str) -> dict:
        """
        Exchange authorization code for access token
        """
        try:
            response = requests.post(
                f"https://{shop}/admin/oauth/access_token",
                data={
                    'client_id': current_app.config['SHOPIFY_API_KEY'],
                    'client_secret': current_app.config['SHOPIFY_API_SECRET'],
                    'code': code
                }
            )
            
            if response.status_code == 200:
                return response.json()
            
            current_app.logger.error(f"Error exchanging code for token: {response.text}")
            return None
        except Exception as e:
            current_app.logger.error(f"Error exchanging code for token: {str(e)}")
            return None
    
    @staticmethod
    def get_shop_info(shop: str, access_token: str) -> dict:
        """
        Get shop information using the access token
        """
        try:
            headers = {'X-Shopify-Access-Token': access_token}
            response = requests.get(
                f"https://{shop}/admin/api/2024-01/shop.json",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()['shop']
            
            current_app.logger.error(f"Error getting shop info: {response.text}")
            return None
        except Exception as e:
            current_app.logger.error(f"Error getting shop info: {str(e)}")
            return None
    
    @staticmethod
    def complete_oauth_flow(shop: str, code: str, state: str) -> dict:
        """
        Complete the entire OAuth flow
        """
        # Verify state parameter and get stored data
        is_valid, user_id, stored_shop = ShopifyOAuthService.verify_state(state)
        if not is_valid or not user_id or stored_shop != shop:
            return {
                'success': False,
                'message': 'Invalid state parameter',
                'data': None
            }
        
        # Exchange code for token
        token_data = ShopifyOAuthService.exchange_code_for_token(shop, code)
        if not token_data:
            return {
                'success': False,
                'message': 'Failed to obtain access token',
                'data': None
            }
        
        access_token = token_data['access_token']
        
        # Get shop information
        shop_info = ShopifyOAuthService.get_shop_info(shop, access_token)
        if not shop_info:
            return {
                'success': False,
                'message': 'Failed to get shop information',
                'data': None
            }
        
        # Clear state from Redis
        ShopifyOAuthService.clear_state(state)
        
        return {
            'success': True,
            'message': 'OAuth completed successfully',
            'data': {
                'shop': shop,
                'access_token': access_token,
                'shop_name': shop_info.get('name'),
                'shop_email': shop_info.get('email'),
                'shop_domain': shop_info.get('domain'),
                'shop_plan': shop_info.get('plan_name'),
                'user_id': user_id
            }
        } 