import requests
import json
from flask import current_app
from app.models.product import Product

class OpenAIService:
    @staticmethod
    def generate_seo_description(product_id: int, keywords: list = None) -> tuple:
        """
        Generate an SEO-optimized description for a product using OpenAI
        Returns: (success: bool, message: str, data: dict)
        """
        try:
            # Get product details
            product = Product.query.get(product_id)
            if not product:
                return False, "Product not found", None
            
            # Prepare prompt for OpenAI
            prompt = f"""
            Create an SEO-optimized product description for the following product:
            
            Product Title: {product.title}
            Original Description: {product.description or 'No description available'}
            
            The description should:
            1. Be engaging and persuasive
            2. Include relevant keywords naturally
            3. Be between 150-300 words
            4. Highlight key features and benefits
            5. Include a call to action
            6. Be formatted with appropriate HTML tags for Shopify
            
            Keywords to include: {', '.join(keywords) if keywords else 'Use relevant keywords based on the product'}
            """
            
            # Call OpenAI API
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {current_app.config['OPENAI_API_KEY']}",
                    "Content-Type": "application/json",
                    "OpenAI-Beta": "assistants=v1"
                },
                json={
                    "model": current_app.config['OPENAI_MODEL'],
                    "messages": [
                        {"role": "system", "content": "You are an expert SEO copywriter specializing in e-commerce product descriptions."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            
            if response.status_code != 200:
                current_app.logger.error(f"Error calling OpenAI API: {response.text}")
                return False, f"Error generating description: {response.status_code}", None
            
            # Extract the generated description
            result = response.json()
            generated_description = result['choices'][0]['message']['content']
            
            return True, "Description generated successfully", {
                'product_id': product_id,
                'optimized_description': generated_description
            }
            
        except Exception as e:
            current_app.logger.error(f"Error in generate_seo_description: {str(e)}")
            return False, f"Error generating description: {str(e)}", None
    
    @staticmethod
    def generate_bulk_seo_descriptions(product_ids: list, keywords: dict = None) -> tuple:
        """
        Generate SEO-optimized descriptions for multiple products
        Returns: (success: bool, message: str, data: list)
        """
        try:
            results = []
            success_count = 0
            error_count = 0
            
            for product_id in product_ids:
                # Get product-specific keywords if available
                product_keywords = keywords.get(product_id, []) if keywords else None
                
                # Generate description for this product
                success, message, data = OpenAIService.generate_seo_description(
                    product_id=product_id,
                    keywords=product_keywords
                )
                
                if success:
                    results.append(data)
                    success_count += 1
                else:
                    results.append({
                        'product_id': product_id,
                        'error': message
                    })
                    error_count += 1
            
            return True, f"Generated {success_count} descriptions, {error_count} errors", results
            
        except Exception as e:
            current_app.logger.error(f"Error in generate_bulk_seo_descriptions: {str(e)}")
            return False, f"Error generating bulk descriptions: {str(e)}", [] 