"""
Odoo MCP Server - Real Invoice Creation Implementation
Creates actual invoices in Odoo ERP system via XML-RPC API
"""

import xmlrpc.client
from datetime import datetime, timedelta

from src.config import PROJECT_ROOT
from src.utils.logging_utils import setup_logging, log_action, log_error

logger = setup_logging()


class OdooMCPServer:
    """Odoo MCP Server - Handles real invoice creation"""

    def __init__(self):
        """Initialize Odoo API connection"""
        self.url = None
        self.db = None
        self.username = None
        self.password = None
        self.uid = None
        self.common = None
        self.models = None
        self.authenticated = False

        self._load_credentials()
        self._authenticate()

    def _load_credentials(self):
        """Load Odoo credentials from environment"""
        import os
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env")

        self.url = os.getenv("ODOO_URL", "http://localhost:8069")
        self.db = os.getenv("ODOO_DB", "")
        self.username = os.getenv("ODOO_USER", "")
        self.password = os.getenv("ODOO_API_KEY", "")

    def _authenticate(self) -> bool:
        """
        Authenticate with Odoo server

        Returns:
            True if authenticated successfully
        """
        try:
            if not all([self.url, self.db, self.username, self.password]):
                logger.warning("⚠️ Odoo credentials incomplete")
                return False

            # Connect to Odoo
            self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})

            if self.uid:
                self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
                self.authenticated = True
                logger.info(f"✅ Odoo authenticated (UID: {self.uid})")
                log_action("odoo_authenticated", self.db, "success")
                return True
            else:
                logger.error("❌ Odoo authentication failed")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to authenticate with Odoo: {e}")
            log_error("odoo_auth_failed", str(e))
            return False

    def create_invoice(
        self,
        customer_name: str,
        amount: float,
        description: str,
        due_days: int = 30,
        products: list = None
    ) -> dict:
        """
        Create invoice in Odoo

        Args:
            customer_name: Customer name
            amount: Invoice amount
            description: Invoice description/items
            due_days: Days until due date
            products: Optional list of product dicts

        Returns:
            Dict with status and invoice ID
        """
        try:
            if not self.authenticated:
                if not self._authenticate():
                    return {
                        "success": False,
                        "error": "Not authenticated with Odoo"
                    }

            # Find or create customer (partner)
            partner_id = self._get_or_create_partner(customer_name)
            if not partner_id:
                return {
                    "success": False,
                    "error": f"Could not find/create partner: {customer_name}"
                }

            # Calculate due date
            due_date = (datetime.now() + timedelta(days=due_days)).strftime("%Y-%m-%d")

            # Prepare invoice data
            invoice_data = {
                'move_type': 'out_invoice',  # Customer invoice
                'partner_id': partner_id,
                'invoice_date': datetime.now().strftime("%Y-%m-%d"),
                'invoice_date_due': due_date,
                'currency_id': 1,  # Assuming USD is ID 1
                'ref': description[:100]
            }

            # Add invoice lines
            if products:
                lines = []
                for product in products:
                    lines.append((0, 0, {
                        'product_id': product.get('id', 1),
                        'name': product.get('name', description),
                        'quantity': product.get('quantity', 1),
                        'price_unit': product.get('price', amount)
                    }))
                invoice_data['invoice_line_ids'] = lines
            else:
                # Single line invoice
                invoice_data['invoice_line_ids'] = [(0, 0, {
                    'product_id': 1,  # Generic product
                    'name': description,
                    'quantity': 1,
                    'price_unit': amount
                })]

            # Create invoice
            invoice_id = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                'account.move',
                'create',
                [invoice_data]
            )

            if invoice_id:
                # Post the invoice to make it official
                self.models.execute_kw(
                    self.db,
                    self.uid,
                    self.password,
                    'account.move',
                    'action_post',
                    [[invoice_id]]
                )

                logger.info(f"✅ Invoice created in Odoo: {invoice_id}")
                log_action(
                    "odoo_invoice_created",
                    customer_name,
                    "success",
                    {
                        "invoice_id": invoice_id,
                        "amount": amount,
                        "due_date": due_date,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

                return {
                    "success": True,
                    "invoice_id": invoice_id,
                    "customer": customer_name,
                    "amount": amount,
                    "due_date": due_date
                }
            else:
                logger.error("❌ Failed to create invoice")
                return {
                    "success": False,
                    "error": "Invoice creation returned no ID"
                }

        except Exception as e:
            logger.error(f"❌ Failed to create invoice: {e}")
            log_error("odoo_invoice_failed", str(e))
            return {"success": False, "error": str(e)}

    def _get_or_create_partner(self, name: str) -> int:
        """
        Get partner ID or create if doesn't exist

        Args:
            name: Partner name

        Returns:
            Partner ID or None
        """
        try:
            # Search for existing partner
            partner_ids = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                'res.partner',
                'search',
                [[('name', '=', name)]]
            )

            if partner_ids:
                return partner_ids[0]

            # Create new partner
            partner_id = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                'res.partner',
                'create',
                [{
                    'name': name,
                    'email': f'{name.lower().replace(" ", ".")}@example.com',
                    'company_type': 'company'
                }]
            )

            return partner_id

        except Exception as e:
            logger.error(f"Failed to get/create partner: {e}")
            return None

    def get_invoice_info(self, invoice_id: int) -> dict:
        """Get invoice info from Odoo"""
        try:
            if not self.authenticated:
                return {"authenticated": False}

            invoice = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                'account.move',
                'read',
                [invoice_id],
                {'fields': ['id', 'name', 'partner_id', 'amount_total', 'invoice_date_due']}
            )

            if invoice:
                return {
                    "authenticated": True,
                    "invoice_id": invoice[0]['id'],
                    "invoice_name": invoice[0]['name'],
                    "partner": invoice[0]['partner_id'][1] if invoice[0]['partner_id'] else "Unknown",
                    "amount": invoice[0]['amount_total'],
                    "due_date": invoice[0]['invoice_date_due']
                }
            return {"authenticated": True, "error": "Invoice not found"}

        except Exception as e:
            logger.error(f"Failed to get invoice info: {e}")
            return {"authenticated": False, "error": str(e)}


# Singleton instance
_odoo_server = None


def get_odoo_server() -> OdooMCPServer:
    """Get or create singleton Odoo server"""
    global _odoo_server
    if _odoo_server is None:
        _odoo_server = OdooMCPServer()
    return _odoo_server


def create_invoice(
    customer_name: str,
    amount: float,
    description: str,
    due_days: int = 30,
    products: list = None
) -> dict:
    """Convenience function to create Odoo invoice"""
    server = get_odoo_server()
    return server.create_invoice(customer_name, amount, description, due_days, products)
