import google.generativeai as genai
from flask import current_app
from app.models.product import Product
import logging

class GeminiService:
    @staticmethod
    def generate_seo_description(product_id: int, keywords: list = None) -> tuple:
        """
        Generate an SEO-optimized description for a product using Google's Gemini
        Returns: (success: bool, message: str, data: dict)
        """
        try:
            # Get product details
            product = Product.query.get(product_id)
            if not product:
                return False, "Product not found", None
            
            # Configure Gemini
            api_key = current_app.config.get('GEMINI_API_KEY')
            model_name = "gemini-1.5-pro"  # Use Gemini 1.5 Pro model
            
            if not api_key:
                current_app.logger.error("Gemini API key is not configured")
                return False, "Error: Gemini API key is not configured", None
                
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            
            # Prepare prompt for Gemini
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
            
            # Generate response using Gemini
            current_app.logger.info(f"Generating description for product {product_id} using Gemini model {model_name}")
            response = model.generate_content(prompt)
            
            if not response or not response.text:
                current_app.logger.error("Error: No response from Gemini API")
                return False, "Error generating description: No response from API", None
            
            generated_description = response.text
            current_app.logger.info(f"Successfully generated description for product {product_id}")
            
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
                success, message, data = GeminiService.generate_seo_description(
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
            
            return True, f"Processed {len(product_ids)} products. Success: {success_count}, Errors: {error_count}", results
            
        except Exception as e:
            current_app.logger.error(f"Error in generate_bulk_seo_descriptions: {str(e)}")
            return False, f"Error in bulk generation: {str(e)}", None 