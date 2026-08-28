"""
Database Scanner - Scans connected databases against compliance rules.
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from .connector import DatabaseConnector


class DatabaseScanner:
    """
    Scans database tables against compliance rules to detect potential violations.
    """
    
    def __init__(self, connector: DatabaseConnector):
        """
        Initialize database scanner.
        
        Args:
            connector: Connected database connector instance
        """
        self.connector = connector
        self.scan_history: List[Dict[str, Any]] = []
    
    async def scan(
        self,
        rules: List[Dict[str, Any]],
        tables: Optional[List[str]] = None,
        sample_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Scan database against provided rules.
        
        Args:
            rules: List of compliance rules to check
            tables: Specific tables to scan (None for all)
            sample_size: Number of rows to sample per table
            
        Returns:
            Scan results with potential violations
        """
        scan_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        logger.info(f"Starting database scan (ID: {scan_id})")
        
        # Get tables to scan
        all_tables = await self.connector.get_tables()
        tables_to_scan = tables if tables else all_tables
        
        # Get database schema
        schema = await self.connector.get_full_schema()
        
        scan_results = {
            "scan_id": scan_id,
            "started_at": datetime.utcnow().isoformat(),
            "tables_scanned": [],
            "rules_checked": len(rules),
            "potential_violations": [],
            "schema": schema
        }
        
        # Scan each table
        for table in tables_to_scan:
            if table not in all_tables:
                logger.warning(f"Table {table} not found, skipping")
                continue
            
            logger.info(f"Scanning table: {table}")
            
            table_results = await self._scan_table(
                table=table,
                rules=rules,
                schema=schema.get(table, {}),
                sample_size=sample_size
            )
            
            scan_results["tables_scanned"].append(table)
            scan_results["potential_violations"].extend(table_results)
        
        scan_results["completed_at"] = datetime.utcnow().isoformat()
        scan_results["total_potential_violations"] = len(scan_results["potential_violations"])
        
        # Store in history
        self.scan_history.append({
            "scan_id": scan_id,
            "timestamp": scan_results["completed_at"],
            "tables": len(tables_to_scan),
            "violations": scan_results["total_potential_violations"]
        })
        
        logger.info(f"Scan complete. Found {scan_results['total_potential_violations']} potential violations")
        
        return scan_results
    
    async def _scan_table(
        self,
        table: str,
        rules: List[Dict[str, Any]],
        schema: Dict[str, Any],
        sample_size: int
    ) -> List[Dict[str, Any]]:
        """
        Scan a single table against rules.
        
        Args:
            table: Table name
            rules: Rules to check
            schema: Table schema information
            sample_size: Number of rows to sample
            
        Returns:
            List of potential violations
        """
        violations = []
        
        # Get column names
        columns = [col['name'] for col in schema.get('columns', [])]
        
        for rule in rules:
            rule_violations = await self._check_rule_against_table(
                table=table,
                rule=rule,
                columns=columns,
                sample_size=sample_size
            )
            violations.extend(rule_violations)
        
        return violations
    
    async def _check_rule_against_table(
        self,
        table: str,
        rule: Dict[str, Any],
        columns: List[str],
        sample_size: int
    ) -> List[Dict[str, Any]]:
        """
        Check a single rule against a table.
        
        Args:
            table: Table name
            rule: Rule to check
            columns: Table columns
            sample_size: Sample size for queries
            
        Returns:
            List of violations for this rule
        """
        violations = []
        rule_type = rule.get('type', 'other')
        
        # Match rule to applicable columns
        applicable_columns = self._find_applicable_columns(rule, columns)
        
        if not applicable_columns and not rule.get('sql_condition'):
            return violations
        
        try:
            # Check rule based on type
            if rule_type == 'data_retention':
                violations.extend(await self._check_data_retention(table, rule, columns, sample_size))
            
            elif rule_type == 'data_encryption':
                violations.extend(await self._check_data_encryption(table, rule, applicable_columns))
            
            elif rule_type == 'data_masking':
                violations.extend(await self._check_data_masking(table, rule, applicable_columns, sample_size))
            
            elif rule_type == 'data_access':
                violations.extend(await self._check_data_access(table, rule, columns))
            
            elif rule_type == 'age_restriction':
                violations.extend(await self._check_age_restriction(table, rule, columns, sample_size))
            
            elif rule_type == 'geographic_restriction':
                violations.extend(await self._check_geographic_restriction(table, rule, columns, sample_size))
            
            elif rule_type == 'audit_logging':
                violations.extend(await self._check_audit_logging(table, rule, columns))
            
            # Generic SQL condition check
            elif rule.get('sql_condition'):
                violations.extend(await self._check_sql_condition(table, rule, sample_size))
            
        except Exception as e:
            logger.warning(f"Error checking rule {rule.get('id')} on table {table}: {e}")
            violations.append({
                "type": "scan_error",
                "table": table,
                "rule_id": rule.get('id'),
                "error": str(e)
            })
        
        return violations
    
    def _find_applicable_columns(
        self,
        rule: Dict[str, Any],
        columns: List[str]
    ) -> List[str]:
        """Find columns that the rule applies to."""
        applicable = []
        
        # Check rule entities
        entities = rule.get('entities', [])
        for entity in entities:
            if '.' in entity:
                _, col = entity.split('.', 1)
                if col in columns:
                    applicable.append(col)
            elif entity in columns:
                applicable.append(entity)
        
        # Check column name patterns for common sensitive fields
        sensitive_patterns = {
            'data_encryption': ['password', 'ssn', 'credit_card', 'account_number', 'secret', 'token', 'key'],
            'data_masking': ['email', 'phone', 'ssn', 'credit_card', 'account', 'address'],
            'consent': ['email', 'marketing', 'consent', 'opted'],
            'age_restriction': ['birthdate', 'birth_date', 'dob', 'date_of_birth', 'age'],
            'geographic_restriction': ['country', 'region', 'location', 'address', 'city', 'state']
        }
        
        rule_type = rule.get('type', '')
        patterns = sensitive_patterns.get(rule_type, [])
        
        for col in columns:
            col_lower = col.lower()
            for pattern in patterns:
                if pattern in col_lower and col not in applicable:
                    applicable.append(col)
        
        return applicable
    
    async def _check_data_retention(
        self,
        table: str,
        rule: Dict[str, Any],
        columns: List[str],
        sample_size: int
    ) -> List[Dict[str, Any]]:
        """Check for data retention policy violations."""
        violations = []
        
        # Look for date columns
        date_columns = [c for c in columns if any(d in c.lower() for d in ['date', 'time', 'created', 'updated', 'modified'])]
        
        if not date_columns:
            return violations
        
        retention_days = int(rule.get('retention_value', 90))
        retention_unit = rule.get('retention_unit', 'days').lower()
        
        # Convert to days
        if 'month' in retention_unit:
            retention_days *= 30
        elif 'year' in retention_unit:
            retention_days *= 365
        
        for date_col in date_columns:
            try:
                # Query for old records
                if self.connector.is_sql:
                    query = f"""
                        SELECT COUNT(*) as count 
                        FROM "{table}" 
                        WHERE "{date_col}" < CURRENT_DATE - INTERVAL '{retention_days} days'
                    """
                    
                    # Try different SQL dialects
                    try:
                        result = await self.connector.execute_query(query)
                    except:
                        # SQLite syntax
                        query = f"""
                            SELECT COUNT(*) as count 
                            FROM "{table}" 
                            WHERE "{date_col}" < date('now', '-{retention_days} days')
                        """
                        result = await self.connector.execute_query(query)
                    
                    if result and result[0]['count'] > 0:
                        violations.append({
                            "type": "data_retention",
                            "table": table,
                            "column": date_col,
                            "rule_id": rule.get('id'),
                            "rule_text": rule.get('text'),
                            "violation_count": result[0]['count'],
                            "details": f"Found {result[0]['count']} records older than {retention_days} days based on {date_col}"
                        })
            except Exception as e:
                logger.debug(f"Could not check retention on {table}.{date_col}: {e}")
        
        return violations
    
    async def _check_data_encryption(
        self,
        table: str,
        rule: Dict[str, Any],
        columns: List[str]
    ) -> List[Dict[str, Any]]:
        """Check for unencrypted sensitive data."""
        violations = []
        
        for col in columns:
            # Sample data to check if it looks encrypted
            try:
                query = f'SELECT "{col}" FROM "{table}" WHERE "{col}" IS NOT NULL LIMIT 10'
                result = await self.connector.execute_query(query)
                
                if result:
                    # Check if values look like plaintext
                    for row in result:
                        value = str(row[col])
                        
                        # Heuristic: encrypted data is usually base64 or hex encoded
                        # Plaintext sensitive data patterns
                        is_plaintext = False
                        
                        # Check for plaintext patterns
                        if 'ssn' in col.lower() and len(value) == 9 and value.isdigit():
                            is_plaintext = True
                        elif 'credit' in col.lower() and len(value) in [15, 16] and value.isdigit():
                            is_plaintext = True
                        elif 'password' in col.lower() and len(value) < 60:  # Hashed passwords are usually 60+ chars
                            is_plaintext = True
                        
                        if is_plaintext:
                            violations.append({
                                "type": "data_encryption",
                                "table": table,
                                "column": col,
                                "rule_id": rule.get('id'),
                                "rule_text": rule.get('text'),
                                "details": f"Column {col} appears to contain unencrypted sensitive data"
                            })
                            break
            except Exception as e:
                logger.debug(f"Could not check encryption on {table}.{col}: {e}")
        
        return violations
    
    async def _check_data_masking(
        self,
        table: str,
        rule: Dict[str, Any],
        columns: List[str],
        sample_size: int
    ) -> List[Dict[str, Any]]:
        """Check for unmasked sensitive data."""
        violations = []
        
        for col in columns:
            try:
                query = f'SELECT "{col}" FROM "{table}" WHERE "{col}" IS NOT NULL LIMIT 10'
                result = await self.connector.execute_query(query)
                
                if result:
                    for row in result:
                        value = str(row[col])
                        is_unmasked = False
                        
                        # Check for unmasked patterns
                        if 'email' in col.lower() and '@' in value and not value.startswith('***'):
                            is_unmasked = True
                        elif 'phone' in col.lower() and len(value.replace('-', '').replace(' ', '')) >= 10:
                            is_unmasked = True
                        
                        if is_unmasked:
                            violations.append({
                                "type": "data_masking",
                                "table": table,
                                "column": col,
                                "rule_id": rule.get('id'),
                                "rule_text": rule.get('text'),
                                "details": f"Column {col} contains unmasked sensitive data"
                            })
                            break
            except Exception as e:
                logger.debug(f"Could not check masking on {table}.{col}: {e}")
        
        return violations
    
    async def _check_data_access(
        self,
        table: str,
        rule: Dict[str, Any],
        columns: List[str]
    ) -> List[Dict[str, Any]]:
        """Check for data access policy violations."""
        # This would typically check database permissions
        # For now, flag if sensitive columns exist without access controls
        violations = []
        
        sensitive_cols = [c for c in columns if any(s in c.lower() for s in ['password', 'secret', 'token', 'key', 'ssn', 'credit'])]
        
        if sensitive_cols:
            violations.append({
                "type": "data_access",
                "table": table,
                "columns": sensitive_cols,
                "rule_id": rule.get('id'),
                "rule_text": rule.get('text'),
                "details": f"Table contains sensitive columns that may need access controls: {', '.join(sensitive_cols)}",
                "requires_review": True
            })
        
        return violations
    
    async def _check_age_restriction(
        self,
        table: str,
        rule: Dict[str, Any],
        columns: List[str],
        sample_size: int
    ) -> List[Dict[str, Any]]:
        """Check for age restriction violations."""
        violations = []
        
        # Find birth date columns
        birth_cols = [c for c in columns if any(b in c.lower() for b in ['birth', 'dob', 'date_of_birth'])]
        
        if not birth_cols:
            return violations
        
        # Extract minimum age from rule
        import re
        min_age = 18  # Default
        match = re.search(r'(\d+)\s*(?:years?)', rule.get('text', ''), re.IGNORECASE)
        if match:
            min_age = int(match.group(1))
        
        for col in birth_cols:
            try:
                if self.connector.is_sql:
                    # PostgreSQL syntax
                    query = f"""
                        SELECT COUNT(*) as count 
                        FROM "{table}" 
                        WHERE EXTRACT(YEAR FROM AGE(CURRENT_DATE, "{col}"::date)) < {min_age}
                    """
                    
                    try:
                        result = await self.connector.execute_query(query)
                    except:
                        # SQLite doesn't have AGE function, skip
                        continue
                    
                    if result and result[0]['count'] > 0:
                        violations.append({
                            "type": "age_restriction",
                            "table": table,
                            "column": col,
                            "rule_id": rule.get('id'),
                            "rule_text": rule.get('text'),
                            "violation_count": result[0]['count'],
                            "details": f"Found {result[0]['count']} records with age below {min_age}"
                        })
            except Exception as e:
                logger.debug(f"Could not check age restriction on {table}.{col}: {e}")
        
        return violations
    
    async def _check_geographic_restriction(
        self,
        table: str,
        rule: Dict[str, Any],
        columns: List[str],
        sample_size: int
    ) -> List[Dict[str, Any]]:
        """Check for geographic restriction violations."""
        violations = []

        # Find location columns
        geo_cols = [c for c in columns if any(g in c.lower() for g in ['country', 'region', 'location', 'state', 'province', 'city'])]

        if not geo_cols:
            return violations

        # Extract restricted regions from rule
        restricted = []
        rule_text = rule.get('text', '').lower()

        # European Union and EEA
        if 'eu' in rule_text or 'eea' in rule_text or 'european' in rule_text:
            restricted.append({'type': 'EU_DATA', 'regions': ['EU', 'EEA', 'AUSTRIA', 'BELGIUM', 'BULGARIA', 'CROATIA', 'CYPRUS', 'CZECH REPUBLIC', 'DENMARK', 'ESTONIA', 'FINLAND', 'FRANCE', 'GERMANY', 'GREECE', 'HUNGARY', 'IRELAND', 'ITALY', 'LATVIA', 'LITHUANIA', 'LUXEMBOURG', 'MALTA', 'NETHERLANDS', 'POLAND', 'PORTUGAL', 'ROMANIA', 'SLOVAKIA', 'SLOVENIA', 'SPAIN', 'SWEDEN', 'ICELAND', 'LIECHTENSTEIN', 'NORWAY']})

        # United States
        if 'us' in rule_text or 'united states' in rule_text or 'usa' in rule_text:
            restricted.append({'type': 'US_DATA', 'regions': ['US', 'USA', 'UNITED STATES', 'ALABAMA', 'ALASKA', 'ARIZONA', 'ARKANSAS', 'CALIFORNIA', 'COLORADO', 'CONNECTICUT', 'DELAWARE', 'FLORIDA', 'GEORGIA', 'HAWAII', 'IDAHO', 'ILLINOIS', 'INDIANA', 'IOWA', 'KANSAS', 'KENTUCKY', 'LOUISIANA', 'MAINE', 'MARYLAND', 'MASSACHUSETTS', 'MICHIGAN', 'MINNESOTA', 'MISSISSIPPI', 'MISSOURI', 'MONTANA', 'NEBRASKA', 'NEVADA', 'NEW HAMPSHIRE', 'NEW JERSEY', 'NEW MEXICO', 'NEW YORK', 'NORTH CAROLINA', 'NORTH DAKOTA', 'OHIO', 'OKLAHOMA', 'OREGON', 'PENNSYLVANIA', 'RHODE ISLAND', 'SOUTH CAROLINA', 'SOUTH DAKOTA', 'TENNESSEE', 'TEXAS', 'UTAH', 'VERMONT', 'VIRGINIA', 'WASHINGTON', 'WEST VIRGINIA', 'WISCONSIN', 'WYOMING']})

        # Canada
        if 'canada' in rule_text or 'ca' in rule_text:
            restricted.append({'type': 'CANADA_DATA', 'regions': ['CANADA', 'ALBERTA', 'BRITISH COLUMBIA', 'MANITOBA', 'NEW BRUNSWICK', 'NEWFOUNDLAND AND LABRADOR', 'NOVA SCOTIA', 'ONTARIO', 'PRINCE EDWARD ISLAND', 'QUEBEC', 'SASKATCHEWAN']})

        # Asia-Pacific
        if 'asia' in rule_text or 'apac' in rule_text:
            restricted.append({'type': 'APAC_DATA', 'regions': ['CHINA', 'JAPAN', 'INDIA', 'AUSTRALIA', 'SINGAPORE', 'SOUTH KOREA']})

        for col in geo_cols:
            try:
                values = await self.connector.execute_query(
                    f'SELECT DISTINCT "{col}" FROM "{table}" WHERE "{col}" IS NOT NULL LIMIT 100'
                )

                if values:
                    unique_values = [str(v[col]).upper().strip() for v in values if v[col] is not None]
                    violations_found = []

                    for restriction in restricted:
                        for value in unique_values:
                            if any(region.upper() in value or value in region.upper() for region in restriction['regions']):
                                violations_found.append({
                                    "type": "geographic_restriction",
                                    "table": table,
                                    "column": col,
                                    "rule_id": rule.get('id'),
                                    "rule_text": rule.get('text'),
                                    "violation_value": value,
                                    "restriction_type": restriction['type'],
                                    "details": f"Geographic data '{value}' found in {col} that violates {restriction['type']} restrictions.",
                                    "requires_review": True
                                })
                                break  # Only report first violation per restriction type per column to avoid duplicates

                    if violations_found:
                        violations.extend(violations_found[:5])  # Limit violations per column to avoid spam

            except Exception as e:
                logger.debug(f"Could not check geographic restriction on {table}.{col}: {e}")

        return violations
    
    async def _check_audit_logging(
        self,
        table: str,
        rule: Dict[str, Any],
        columns: List[str]
    ) -> List[Dict[str, Any]]:
        """Check for audit logging compliance."""
        violations = []
        
        # Check if table has audit columns
        audit_cols = ['created_at', 'updated_at', 'modified_at', 'created_by', 'modified_by', 'audit_log']
        has_audit = any(any(a in c.lower() for a in audit_cols) for c in columns)
        
        if not has_audit:
            violations.append({
                "type": "audit_logging",
                "table": table,
                "rule_id": rule.get('id'),
                "rule_text": rule.get('text'),
                "details": f"Table {table} lacks audit columns (created_at, updated_at, etc.)",
                "requires_review": True
            })
        
        return violations
    
    async def _check_sql_condition(
        self,
        table: str,
        rule: Dict[str, Any],
        sample_size: int
    ) -> List[Dict[str, Any]]:
        """Check using custom SQL condition from rule."""
        violations = []
        
        sql_condition = rule.get('sql_condition')
        if not sql_condition:
            return violations
        
        try:
            query = f'SELECT COUNT(*) as count FROM "{table}" WHERE {sql_condition}'
            result = await self.connector.execute_query(query)
            
            if result and result[0]['count'] > 0:
                violations.append({
                    "type": rule.get('type', 'custom'),
                    "table": table,
                    "rule_id": rule.get('id'),
                    "rule_text": rule.get('text'),
                    "violation_count": result[0]['count'],
                    "sql_condition": sql_condition,
                    "details": f"Found {result[0]['count']} records matching violation condition"
                })
        except Exception as e:
            logger.debug(f"SQL condition check failed on {table}: {e}")
        
        return violations
