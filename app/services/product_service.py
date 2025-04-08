import requests
from flask import current_app
from app import db
from app.models.product import Product
from app.models.optimized_description import OptimizedDescription, DescriptionStatus
from app.services.store_service import StoreService
from app.services.crud import CRUD
from datetime import datetime
import pytz

class ProductService:
    @staticmethod
    def _convert_shopify_datetime(datetime_str: str) -> datetime:
        """
        Convert Shopify datetime string to Python datetime object
        """
        if not datetime_str:
            return None
        try:
            # Parse the datetime string and convert to UTC
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.astimezone(pytz.UTC)
        except Exception as e:
            current_app.logger.error(f"Error converting datetime: {str(e)}")
            return None

    @staticmethod
    def fetch_products_from_shopify(store_id: int, limit: int = 250) -> tuple:
        """
        Fetch products from Shopify for a specific store
        Returns: (success: bool, message: str, data: list)
        """
        try:
            # Get store details
            store = StoreService.get_store_by_id(store_id)
            if not store:
                return False, "Store not found", []
            
            # Prepare Shopify API request
            headers = {
                'X-Shopify-Access-Token': store.access_token,
                'Content-Type': 'application/json'
            }
            
            # Fetch products from Shopify
            response = requests.get(
                f"https://{store.store_url}/admin/api/2024-01/products.json?limit={limit}",
                headers=headers
            )
            
            if response.status_code != 200:
                current_app.logger.error(f"Error fetching products from Shopify: {response.text}")
                return False, f"Error fetching products: {response.status_code}", []
            
            shopify_products = response.json().get('products', [])
            
            # Process and store products
            products_added = 0
            products_updated = 0
            
            for shopify_product in shopify_products:
                # Check if product already exists
                existing_product = Product.query.filter_by(
                    store_id=store_id,
                    shopify_product_id=shopify_product['id']
                ).first()
                
                if existing_product:
                    # Update existing product
                    product_data = {
                        'title': shopify_product['title'],
                        'description': shopify_product.get('body_html', ''),
                        'vendor': shopify_product.get('vendor', ''),
                        'product_type': shopify_product.get('product_type', ''),
                        'handle': shopify_product.get('handle', ''),
                        'status': shopify_product.get('status', 'active'),
                        'shopify_updated_at': ProductService._convert_shopify_datetime(shopify_product.get('updated_at'))
                    }
                    CRUD.update(Product, {'id': existing_product.id}, product_data)
                    products_updated += 1
                else:
                    # Create new product
                    product_data = {
                        'store_id': store_id,
                        'shopify_product_id': shopify_product['id'],
                        'title': shopify_product['title'],
                        'description': shopify_product.get('body_html', ''),
                        'vendor': shopify_product.get('vendor', ''),
                        'product_type': shopify_product.get('product_type', ''),
                        'handle': shopify_product.get('handle', ''),
                        'status': shopify_product.get('status', 'active'),
                        'shopify_created_at': ProductService._convert_shopify_datetime(shopify_product.get('created_at')),
                        'shopify_updated_at': ProductService._convert_shopify_datetime(shopify_product.get('updated_at'))
                    }
                    CRUD.create(Product, product_data)
                    products_added += 1
            
            return True, f"Products synced successfully. Added: {products_added}, Updated: {products_updated}", {
                'added': products_added,
                'updated': products_updated
            }
        except Exception as e:
            current_app.logger.error(f"Error syncing products: {str(e)}")
            return False, f"Error syncing products: {str(e)}", []

    @staticmethod
    def get_store_products(store_id: int, page: int = 1, per_page: int = 20) -> tuple:
        """
        Get all products for a store with pagination
        Returns: (products: list, total: int, pages: int)
        """
        try:
            # Get paginated products
            pagination = Product.query.filter_by(store_id=store_id).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            products = [{
                'id': product.id,
                'title': product.title,
                'description': product.description,
                'vendor': product.vendor,
                'product_type': product.product_type,
                'handle': product.handle,
                'status': product.status,
                'created_at': product.created_at.isoformat() if product.created_at else None,
                'updated_at': product.updated_at.isoformat() if product.updated_at else None
            } for product in pagination.items]
            
            return products, pagination.total, pagination.pages
        except Exception as e:
            current_app.logger.error(f"Error getting store products: {str(e)}")
            return [], 0, 0

    @staticmethod
    def get_product_by_id(product_id: int) -> dict:
        """
        Get a product by ID
        """
        try:
            product = Product.query.get(product_id)
            if not product:
                return None
                
            return {
                'id': product.id,
                'store_id': product.store_id,
                'shopify_product_id': product.shopify_product_id,
                'title': product.title,
                'description': product.description,
                'vendor': product.vendor,
                'product_type': product.product_type,
                'handle': product.handle,
                'status': product.status,
                'created_at': product.created_at.isoformat() if product.created_at else None,
                'updated_at': product.updated_at.isoformat() if product.updated_at else None
            }
        except Exception as e:
            current_app.logger.error(f"Error getting product by ID: {str(e)}")
            return None

    @staticmethod
    def get_product_optimized_descriptions(product_id: int) -> list:
        """
        Get all optimized descriptions for a product
        """
        try:
            descriptions = OptimizedDescription.query.filter_by(product_id=product_id).all()
            return [{
                'id': desc.id,
                'product_id': desc.product_id,
                'original_description': desc.original_description,
                'optimized_description': desc.optimized_description,
                'status': desc.status.value,
                'created_at': desc.created_at.isoformat() if desc.created_at else None,
                'updated_at': desc.updated_at.isoformat() if desc.updated_at else None
            } for desc in descriptions]
        except Exception as e:
            current_app.logger.error(f"Error getting product descriptions: {str(e)}")
            return []

    @staticmethod
    def create_optimized_description(product_id: int, optimized_description: str) -> tuple:
        """
        Create a new optimized description for a product
        """
        try:
            # Get product
            product = Product.query.get(product_id)
            if not product:
                return False, "Product not found", None
                
            # Create optimized description
            description_data = {
                'product_id': product_id,
                'original_description': product.description,
                'optimized_description': optimized_description,
                'status': DescriptionStatus.DRAFT
            }
            
            new_description = CRUD.create(OptimizedDescription, description_data)
            
            return True, "Optimized description created successfully", {
                'id': new_description.id,
                'product_id': new_description.product_id,
                'original_description': new_description.original_description,
                'optimized_description': new_description.optimized_description,
                'status': new_description.status.value,
                'created_at': new_description.created_at.isoformat() if new_description.created_at else None
            }
        except Exception as e:
            current_app.logger.error(f"Error creating optimized description: {str(e)}")
            return False, f"Error creating optimized description: {str(e)}", None

    @staticmethod
    def update_optimized_description(description_id: int, optimized_description: str) -> tuple:
        """
        Update an optimized description
        """
        try:
            # Get description
            description = OptimizedDescription.query.get(description_id)
            if not description:
                return False, "Description not found", None
                
            # Update description
            update_data = {
                'optimized_description': optimized_description,
                'status': DescriptionStatus.DRAFT
            }
            
            CRUD.update(OptimizedDescription, {'id': description_id}, update_data)
            
            # Get updated description
            updated_description = OptimizedDescription.query.get(description_id)
            
            return True, "Optimized description updated successfully", {
                'id': updated_description.id,
                'product_id': updated_description.product_id,
                'original_description': updated_description.original_description,
                'optimized_description': updated_description.optimized_description,
                'status': updated_description.status.value,
                'updated_at': updated_description.updated_at.isoformat() if updated_description.updated_at else None
            }
        except Exception as e:
            current_app.logger.error(f"Error updating optimized description: {str(e)}")
            return False, f"Error updating optimized description: {str(e)}", None

    @staticmethod
    def deploy_optimized_description(description_id: int) -> tuple:
        """
        Deploy an optimized description to Shopify
        """
        try:
            # Get description
            description = OptimizedDescription.query.get(description_id)
            if not description:
                return False, "Description not found", None
                
            # Get product
            product = Product.query.get(description.product_id)
            if not product:
                return False, "Product not found", None
                
            # Get store
            store = StoreService.get_store_by_id(product.store_id)
            if not store:
                return False, "Store not found", None
                
            # Prepare Shopify API request
            headers = {
                'X-Shopify-Access-Token': store.access_token,
                'Content-Type': 'application/json'
            }
            
            # Update product in Shopify
            data = {
                'product': {
                    'id': product.shopify_product_id,
                    'body_html': description.optimized_description
                }
            }
            
            response = requests.put(
                f"https://{store.store_url}/admin/api/2024-01/products/{product.shopify_product_id}.json",
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                current_app.logger.error(f"Error deploying description to Shopify: {response.text}")
                return False, f"Error deploying description: {response.status_code}", None
                
            # Update description status
            update_data = {'status': DescriptionStatus.DEPLOYED}
            CRUD.update(OptimizedDescription, {'id': description_id}, update_data)
            
            return True, "Description deployed successfully", None
        except Exception as e:
            current_app.logger.error(f"Error deploying description: {str(e)}")
            return False, f"Error deploying description: {str(e)}", None

    @staticmethod
    def delete_optimized_description(description_id: int) -> tuple:
        """
        Delete an optimized description
        """
        try:
            # Get description
            description = OptimizedDescription.query.get(description_id)
            if not description:
                return False, "Description not found", None
                
            # Delete description
            CRUD.delete(OptimizedDescription, {'id': description_id})
            
            return True, "Description deleted successfully", None
        except Exception as e:
            current_app.logger.error(f"Error deleting description: {str(e)}")
            return False, f"Error deleting description: {str(e)}", None 