from typing import Optional, Tuple, List
import requests
from flask import current_app
from app.models.store import Store
from app import db
from app.services.crud import CRUD

class StoreService:
    @staticmethod
    def verify_shopify_token(shop_url: str, access_token: str) -> bool:
        """
        Verify if the Shopify access token is valid
        """
        try:
            headers = {'X-Shopify-Access-Token': access_token}
            response = requests.get(
                f"https://{shop_url}/admin/api/2024-01/shop.json",
                headers=headers
            )
            return response.status_code == 200
        except Exception as e:
            current_app.logger.error(f"Error verifying Shopify token: {str(e)}")
            return False

    @staticmethod
    def add_store(user_id: int, store_url: str, access_token: str, store_name: str = None) -> tuple:
        """
        Add a new Shopify store for a user
        """
        try:
            # Verify if store already exists for this user
            existing_store = Store.query.filter_by(
                user_id=user_id,
                store_url=store_url
            ).first()

            if existing_store:
                return False, "Store already exists for this user", None

            # Create new store using CRUD
            store_data = {
                'user_id': user_id,
                'store_url': store_url,
                'access_token': access_token,
                'store_name': store_name or store_url
            }
            
            new_store = CRUD.create(Store, store_data)

            return True, "Store added successfully", {
                'id': new_store.id,
                'store_url': new_store.store_url,
                'store_name': new_store.store_name
            }
        except Exception as e:
            current_app.logger.error(f"Error adding store: {str(e)}")
            return False, f"Error adding store: {str(e)}", None

    @staticmethod
    def get_user_stores(user_id: int) -> list:
        """
        Get all stores for a user
        """
        try:
            stores = Store.query.filter_by(user_id=user_id).all()
            return [{
                'id': store.id,
                'store_url': store.store_url,
                'store_name': store.store_name,
                'created_at': store.created_at.isoformat() if store.created_at else None,
                'updated_at': store.updated_at.isoformat() if store.updated_at else None
            } for store in stores]
        except Exception as e:
            current_app.logger.error(f"Error getting user stores: {str(e)}")
            return []

    @staticmethod
    def update_store(user_id: int, store_id: int, store_name: str) -> tuple:
        """
        Update a store's name
        """
        try:
            # Check if store exists and belongs to user
            store = Store.query.filter_by(
                id=store_id,
                user_id=user_id
            ).first()
            
            if not store:
                return False, "Store not found", None
            
            # Update store using CRUD
            update_data = {'store_name': store_name}
            CRUD.update(Store, {'id': store_id}, update_data)
            
            return True, "Store updated successfully", {
                'id': store.id,
                'store_url': store.store_url,
                'store_name': store_name
            }
        except Exception as e:
            current_app.logger.error(f"Error updating store: {str(e)}")
            return False, f"Error updating store: {str(e)}", None

    @staticmethod
    def delete_store(user_id: int, store_id: int) -> tuple:
        """
        Delete a store
        """
        try:
            # Check if store exists and belongs to user
            store = Store.query.filter_by(
                id=store_id,
                user_id=user_id
            ).first()
            
            if not store:
                return False, "Store not found", None
            
            # Delete store using CRUD
            CRUD.delete(Store, {'id': store_id})
            
            return True, "Store deleted successfully", None
        except Exception as e:
            current_app.logger.error(f"Error deleting store: {str(e)}")
            return False, f"Error deleting store: {str(e)}", None
            
    @staticmethod
    def get_store_by_id(store_id: int) -> Optional[Store]:
        """
        Get a store by ID
        """
        try:
            return Store.query.get(store_id)
        except Exception as e:
            current_app.logger.error(f"Error getting store by ID: {str(e)}")
            return None 