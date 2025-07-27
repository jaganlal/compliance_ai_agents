"""
Mock data generator for development and testing
"""

import random
from datetime import datetime, date, timedelta
from typing import List
from faker import Faker

from models.compliance_models import Contract, Planogram, StoreImage

fake = Faker()

class MockDataGenerator:
    """Generate mock data for testing and development."""
  
    def __init__(self):
        self.store_ids = [f"STORE_{i:04d}" for i in range(1, 21)]
        self.product_categories = [
            "CPG Classic", "Diet Coke", "Coke Zero", "Sprite", 
            "Fanta Orange", "Dasani Water", "Powerade", "Minute Maid"
        ]
        self.sections = [
            "beverage_aisle", "checkout", "end_cap", "cooler", 
            "promotional_display", "entrance"
        ]
  
    def generate_contracts(self, count: int = 5) -> List[Contract]:
        """Generate mock contracts."""
        contracts = []
      
        for i in range(count):
            contract = Contract(
                name=f"Retail Agreement {fake.company()} - {fake.year()}",
                store_id=random.choice(self.store_ids),
                effective_date=fake.date_between(start_date='-1y', end_date='today'),
                expiry_date=fake.date_between(start_date='today', end_date='+1y'),
                content=self._generate_contract_content(),
                compliance_rules=self._generate_compliance_rules(),
                created_at=fake.date_time_between(start_date='-1y', end_date='now'),
                updated_at=fake.date_time_between(start_date='-30d', end_date='now')
            )
            contracts.append(contract)
      
        return contracts
  
    def generate_planograms(self, count: int = 10) -> List[Planogram]:
        """Generate mock planograms."""
        planograms = []
      
        for i in range(count):
            planogram = Planogram(
                name=f"Planogram {fake.word().title()} {fake.random_int(1, 100)}",
                store_id=random.choice(self.store_ids),
                section=random.choice(self.sections),
                layout_data=self._generate_layout_data(),
                effective_date=fake.date_between(start_date='-6m', end_date='today'),
                version=f"{fake.random_int(1, 5)}.{fake.random_int(0, 9)}",
                created_at=fake.date_time_between(start_date='-6m', end_date='now'),
                updated_at=fake.date_time_between(start_date='-30d', end_date='now')
            )
            planograms.append(planogram)
      
        return planograms
  
    def generate_store_images(self, count: int = 20) -> List[StoreImage]:
        """Generate mock store images."""
        images = []
      
        for i in range(count):
            image = StoreImage(
                store_id=random.choice(self.store_ids),
                image_url=f"https://mock-storage.blob.core.windows.net/images/store_image_{i:04d}.jpg",
                captured_at=fake.date_time_between(start_date='-7d', end_date='now'),
                section=random.choice(self.sections),
                processed=fake.boolean(chance_of_getting_true=70),
                analysis_result=self._generate_analysis_result() if fake.boolean(chance_of_getting_true=70) else None
            )
            images.append(image)
      
        return images
  
    def _generate_contract_content(self) -> str:
        """Generate mock contract content."""
        return f"""
        RETAIL PRODUCT PLACEMENT AGREEMENT
      
        This agreement outlines the terms for CPG product placement and compliance requirements.
      
        SECTION 1: PRODUCT PLACEMENT
        - CPG products must occupy minimum 60% of beverage shelf space
        - Products must be placed at eye level (shelves 2-4)
        - Promotional displays must be maintained for minimum 30 days
      
        SECTION 2: STOCKING REQUIREMENTS
        - Minimum stock levels: {fake.random_int(50, 200)} units per product
        - Restocking frequency: {fake.random_int(2, 7)} times per week
        - Out-of-stock tolerance: Maximum {fake.random_int(2, 8)} hours
      
        SECTION 3: PROMOTIONAL COMPLIANCE
        - End-cap displays required during promotional periods
        - Pricing compliance with agreed promotional rates
        - Point-of-sale materials must be displayed as specified
      
        Effective Date: {fake.date_between(start_date='-1y', end_date='today')}
        Agreement ID: {fake.uuid4()}
        """
  
    def _generate_compliance_rules(self) -> List[dict]:
        """Generate mock compliance rules."""
        return [
            {
                "rule_id": fake.uuid4(),
                "type": "shelf_space",
                "requirement": "minimum_60_percent",
                "threshold": 60.0,
                "penalty": "tier_1"
            },
            {
                "rule_id": fake.uuid4(),
                "type": "stock_level", 
                "requirement": f"minimum_{fake.random_int(50, 200)}_units",
                "threshold": fake.random_int(50, 200),
                "penalty": "tier_2"
            },
            {
                "rule_id": fake.uuid4(),
                "type": "placement",
                "requirement": "eye_level_placement",
                "shelves": [2, 3, 4],
                "penalty": "tier_1"
            },
            {
                "rule_id": fake.uuid4(),
                "type": "promotional_display",
                "requirement": "end_cap_during_promo",
                "duration_days": 30,
                "penalty": "tier_3"
            }
        ]
  
    def _generate_layout_data(self) -> dict:
        """Generate mock planogram layout data."""
        return {
            "shelves": [
                {
                    "shelf_id": i,
                    "height": fake.random_int(100, 200),
                    "products": [
                        {
                            "product": random.choice(self.product_categories),
                            "position": j,
                            "width": fake.random_int(10, 30),
                            "quantity": fake.random_int(5, 20)
                        }
                        for j in range(fake.random_int(3, 8))
                    ]
                }
                for i in range(1, fake.random_int(4, 7))
            ],
            "total_width": fake.random_int(200, 400),
            "total_height": fake.random_int(150, 300),
            "compliance_zones": [
                {
                    "zone": "primary",
                    "shelves": [2, 3, 4],
                    "min_percentage": 60
                },
                {
                    "zone": "secondary", 
                    "shelves": [1, 5],
                    "min_percentage": 20
                }
            ]
        }
  
    def _generate_analysis_result(self) -> dict:
        """Generate mock image analysis result."""
        return {
            "detected_products": [
                {
                    "product": random.choice(self.product_categories),
                    "confidence": round(random.uniform(0.7, 0.99), 2),
                    "bbox": [
                        fake.random_int(0, 100),
                        fake.random_int(0, 100), 
                        fake.random_int(100, 200),
                        fake.random_int(100, 200)
                    ],
                    "shelf": fake.random_int(1, 5)
                }
                for _ in range(fake.random_int(3, 12))
            ],
            "compliance_score": round(random.uniform(70.0, 95.0), 1),
            "violations": [
                {
                    "type": random.choice(["placement", "stock_level", "promotional"]),
                    "severity": random.choice(["low", "medium", "high"]),
                    "description": fake.sentence()
                }
                for _ in range(fake.random_int(0, 3))
            ],
            "processed_at": fake.date_time_between(start_date='-1d', end_date='now').isoformat()
        }