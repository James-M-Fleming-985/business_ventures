"""
End-to-End tests for Interactive Feasibility Tool (FEATURE-001)

Tests cover complete user workflows including:
- Creating and submitting feasibility assessments
- Viewing and filtering results
- Exporting reports
- Error handling and edge cases
"""

import pytest
from datetime import datetime, timedelta
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class TestInteractiveFeasibilityToolE2E:
    """End-to-end tests for the Interactive Feasibility Tool"""

    @pytest.fixture(scope="class")
    def driver(self):
        """Setup and teardown for WebDriver"""
        driver = webdriver.Chrome()
        driver.maximize_window()
        driver.implicitly_wait(10)
        yield driver
        driver.quit()

    @pytest.fixture(scope="function")
    def login(self, driver):
        """Login fixture for authenticated tests"""
        driver.get("http://localhost:8000/login")
        driver.find_element(By.ID, "username").send_keys("testuser@example.com")
        driver.find_element(By.ID, "password").send_keys("TestPassword123!")
        driver.find_element(By.ID, "login-button").click()
        
        # Wait for dashboard to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard"))
        )
        yield
        # Logout after test
        driver.find_element(By.ID, "logout-button").click()

    def test_complete_feasibility_assessment_workflow(self, driver, login):
        """
        Test E2E Scenario 1: Complete feasibility assessment creation and submission
        
        Acceptance Criteria:
        - User can access the feasibility tool
        - All required fields must be filled
        - Assessment is saved and can be retrieved
        - Results are calculated correctly
        - Email notification is sent
        """
        # Navigate to feasibility tool
        driver.get("http://localhost:8000/feasibility-tool")
        
        # Verify page loaded
        assert "Interactive Feasibility Tool" in driver.title
        
        # Fill in project details
        project_name = f"Test Project {datetime.now().strftime('%Y%m%d%H%M%S')}"
        driver.find_element(By.ID, "project-name").send_keys(project_name)
        driver.find_element(By.ID, "project-description").send_keys(
            "This is a comprehensive test project for E2E testing of the feasibility tool. "
            "It includes multiple components and requirements."
        )
        
        # Select project type
        project_type = Select(driver.find_element(By.ID, "project-type"))
        project_type.select_by_value("software-development")
        
        # Fill in timeline
        start_date = datetime.now() + timedelta(days=30)
        end_date = datetime.now() + timedelta(days=180)
        driver.find_element(By.ID, "start-date").send_keys(
            start_date.strftime("%m/%d/%Y")
        )
        driver.find_element(By.ID, "end-date").send_keys(
            end_date.strftime("%m/%d/%Y")
        )
        
        # Fill in budget information
        driver.find_element(By.ID, "estimated-budget").send_keys("500000")
        currency = Select(driver.find_element(By.ID, "currency"))
        currency.select_by_value("USD")
        
        # Fill in resources
        driver.find_element(By.ID, "team-size").send_keys("15")
        driver.find_element(By.ID, "required-skills").send_keys(
            "Python, React, AWS, DevOps, Project Management"
        )
        
        # Fill in technical requirements
        driver.find_element(By.ID, "tech-stack").send_keys(
            "Python 3.9, React 18, PostgreSQL, Redis, Docker, Kubernetes"
        )
        driver.find_element(By.ID, "infrastructure-needs").send_keys(
            "AWS EC2, RDS, S3, CloudFront, Load Balancer"
        )
        
        # Add risk factors
        driver.find_element(By.ID, "add-risk-button").click()
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "risk-item"))
        )
        driver.find_element(By.NAME, "risk-description").send_keys(
            "Potential delays in third-party API integration"
        )
        risk_level = Select(driver.find_element(By.NAME, "risk-level"))
        risk_level.select_by_value("medium")
        
        # Add success criteria
        driver.find_element(By.ID, "success-criteria").send_keys(
            "1. System handles 10,000 concurrent users\n"
            "2. 99.9% uptime\n"
            "3. Response time under 200ms\n"
            "4. All security requirements met"
        )
        
        # Submit assessment
        submit_button = driver.find_element(By.ID, "submit-assessment")
        driver.execute_script("arguments[0].scrollIntoView();", submit_button)
        submit_button.click()
        
        # Wait for results
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "assessment-results"))
        )
        
        # Verify results are displayed
        results_section = driver.find_element(By.ID, "assessment-results")
        assert results_section.is_displayed()
        
        # Check feasibility score
        feasibility_score = driver.find_element(By.ID, "feasibility-score").text
        assert feasibility_score.replace("%", "").isdigit()
        assert 0 <= int(feasibility_score.replace("%", "")) <= 100
        
        # Verify recommendations are shown
        recommendations = driver.find_elements(By.CLASS_NAME, "recommendation-item")
        assert len(recommendations) > 0
        
        # Verify assessment is saved
        assessment_id = driver.find_element(By.ID, "assessment-id").text
        assert assessment_id
        
        # Navigate to assessments list
        driver.find_element(By.ID, "my-assessments-link").click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "assessments-table"))
        )
        
        # Verify our assessment appears in the list
        assessment_found = False
        table_rows = driver.find_elements(By.CSS_SELECTOR, "#assessments-table tbody tr")
        for row in table_rows:
            if project_name in row.text:
                assessment_found = True
                # Verify status
                status = row.find_element(By.CLASS_NAME, "status-badge").text
                assert status == "Completed"
                break
        
        assert assessment_found, f"Assessment '{project_name}' not found in list"
        
        # Verify email notification (check notification banner)
        notification = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "notification-success"))
        )
        assert "Email notification sent" in notification.text

    def test_feasibility_assessment_with_validation_errors(self, driver, login):
        """
        Test E2E Scenario 2: Form validation and error handling
        
        Acceptance Criteria:
        - Required fields show validation errors
        - Invalid data formats are rejected
        - User can correct errors and resubmit
        - Appropriate error messages are displayed
        """
        # Navigate to feasibility tool
        driver.get("http://localhost:8000/feasibility-tool")
        
        # Try to submit empty form
        submit_button = driver.find_element(By.ID, "submit-assessment")
        submit_button.click()
        
        # Verify validation errors appear
        errors = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "field-error"))
        )
        assert len(errors) > 0
        
        # Check specific validation messages
        project_name_error = driver.find_element(
            By.CSS_SELECTOR, "#project-name + .field-error"
        ).text
        assert "Project name is required" in project_name_error
        
        # Fill in invalid data
        driver.find_element(By.ID, "project-name").send_keys("a")  # Too short
        driver.find_element(By.ID, "estimated-budget").send_keys("-1000")  # Negative
        driver.find_element(By.ID, "team-size").send_keys("0")  # Invalid size
        
        # Set invalid date range (end before start)
        driver.find_element(By.ID, "start-date").send_keys("12/31/2024")
        driver.find_element(By.ID, "end-date").send_keys("01/01/2024")
        
        # Submit again
        submit_button.click()
        
        # Verify new validation errors
        time.sleep(1)  # Wait for validation
        
        name_error = driver.find_element(
            By.CSS_SELECTOR, "#project-name + .field-error"
        ).text
        assert "at least 3 characters" in name_error.lower()
        
        budget_error = driver.find_element(
            By.CSS_SELECTOR, "#estimated-budget + .field-error"
        ).text
        assert "positive" in budget_error.lower() or "greater than 0" in budget_error.lower()
        
        date_error = driver.find_element(
            By.CSS_SELECTOR, "#end-date + .field-error"
        ).text
        assert "after start date" in date_error.lower()
        
        # Fix errors and fill valid data
        driver.find_element(By.ID, "project-name").clear()
        driver.find_element(By.ID, "project-name").send_keys("Valid Test Project")
        
        driver.find_element(By.ID, "project-description").send_keys(
            "Valid project description for testing"
        )
        
        project_type = Select(driver.find_element(By.ID, "project-type"))
        project_type.select_by_value("infrastructure")
        
        driver.find_element(By.ID, "estimated-budget").clear()
        driver.find_element(By.ID, "estimated-budget").send_keys("100000")
        
        driver.find_element(By.ID, "team-size").clear()
        driver.find_element(By.ID, "team-size").send_keys("5")
        
        # Fix dates
        driver.find_element(By.ID, "start-date").clear()
        driver.find_element(By.ID, "start-date").send_keys("01/01/2024")
        driver.find_element(By.ID, "end-date").clear()
        driver.find_element(By.ID, "end-date").send_keys("12/31/2024")
        
        # Fill remaining required fields
        currency = Select(driver.find_element(By.ID, "currency"))
        currency.select_by_value("EUR")
        
        driver.find_element(By.ID, "required-skills").send_keys("Testing, QA")
        driver.find_element(By.ID, "tech-stack").send_keys("Python, Jenkins")
        driver.find_element(By.ID, "success-criteria").send_keys("Project completed on time")
        
        # Submit corrected form
        submit_button.click()
        
        # Verify successful submission
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "assessment-results"))
        )
        assert driver.find_element(By.ID, "assessment-results").is_displayed()

    def test_assessment_report_generation_and_export(self, driver, login):
        """
        Test E2E Scenario 3: Generate and export feasibility assessment report
        
        Acceptance Criteria:
        - User can generate reports in multiple formats
        - Reports contain all assessment data
        - Export functionality works correctly
        - Reports can be shared via email
        - Report history is maintained
        """
        # First create an assessment
        driver.get("http://localhost:8000/feasibility-tool")
        
        # Fill in minimum required fields for quick assessment
        project_name = f"Export Test {datetime.now().strftime('%Y%m%d%H%M%S')}"
        driver.find_element(By.ID, "project-name").send_keys(project_name)
        driver.find_element(By.ID, "project-description").send_keys(
            "Test project for report export functionality"
        )
        
        Select(driver.find_element(By.ID, "project-type")).select_by_value("research")
        
        driver.find_element(By.ID, "start-date").send_keys("03/01/2024")
        driver.find_element(By.ID, "end-date").send_keys("08/01/2024")
        
        driver.find_element(By.ID, "estimated-budget").send_keys("250000")
        Select(driver.find_element(By.ID, "currency")).select_by_value("GBP")
        
        driver.find_element(By.ID, "team-size").send_keys("8")
        driver.find_element(By.ID, "required-skills").send_keys("Research, Analysis, Documentation")
        driver.find_element(By.ID, "tech-stack").send_keys("SPSS, R, Python")
        driver.find_element(By.ID, "success-criteria").send_keys("Research objectives met")
        
        # Submit assessment
        driver.find_element(By.ID, "submit-assessment").click()
        
        # Wait for results
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "assessment-results"))
        )
        
        # Click generate report button
        generate_report_btn = driver.find_element(By.ID, "generate-report-button")
        driver.execute_script("arguments[0].scrollIntoView();", generate_report_btn)
        generate_report_btn.click()
        
        # Wait for report options modal
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "report-options-modal"))
        )
        
        # Test PDF export
        driver.find_element(By.ID, "report-format-pdf").click()
        driver.find_element(By.ID, "include-charts").click()  # Include visual charts
        driver.find_element(By.ID, "include-recommendations").click()
        driver.find_element(By.ID, "generate-report-confirm").click()
        
        # Wait for download to start (check for success message)
        download_success = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "download-success"))
        )
        assert "PDF report generated" in download_success.text
        
        # Test Excel export
        generate_report_btn.click()
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "report-options-modal"))
        )
        driver.find_element(By.ID, "report-format-excel").click()
        driver.find_element(By.ID, "include-raw-data").click()
        driver.find_element(By.ID, "generate-report-confirm").click()
        
        # Verify Excel generation
        excel_success = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "download-success"))
        )
        assert "Excel report generated" in excel_success.text
        
        # Test email sharing
        driver.find_element(By.ID, "share-report-button").click()
        
        # Fill email share form
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "share-modal"))
        )
        driver.find_element(By.ID, "recipient-email").send_keys(
            "stakeholder@example.com"
        )
        driver.find_element(By.ID, "email-subject").clear()
        driver.find_element(By.ID, "email-subject").send_keys(
            f"Feasibility Report: {project_name}"
        )
        driver.find_element(By.ID, "email-message").send_keys(
            "Please find attached the feasibility assessment report for review."
        )
        
        # Select report format to share
        Select(driver.find_element(By.ID, "share-format")).select_by_value("pdf")
        
        # Send email
        driver.find_element(By.ID, "send-report-email").click()
        
        # Verify email sent
        email_confirmation = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "email-sent-success"))
        )
        assert "Report sent successfully" in email_confirmation.text
        
        # Navigate to report history
        driver.find_element(By.ID, "report-history-link").click()
        
        # Verify reports are listed
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "reports-history-table"))
        )
        
        # Check our reports appear
        report_rows = driver.find_elements(
            By.CSS_SELECTOR, "#reports-history-table tbody tr"
        )
        pdf_found = False
        excel_found = False
        
        for row in report_rows:
            row_text = row.text
            if project_name in row_text:
                if "PDF" in row_text:
                    pdf_found = True
                    # Verify download link exists
                    download_link = row.find_element(By.CLASS_NAME, "download-link")
                    assert download_link.is_enabled()
                elif "Excel" in row_text:
                    excel_found = True
        
        assert pdf_found, "PDF report not found in history"
        assert excel_found, "Excel report not found in history"
        
        # Test report preview
        preview_button = driver.find_element(
            By.CSS_SELECTOR, "#reports-history-table .preview-button"
        )
        preview_button.click()
        
        # Verify preview modal opens
        preview_modal = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "report-preview-modal"))
        )
        assert preview_modal.is_displayed()
        
        # Verify report content in preview
        preview_content = driver.find_element(By.ID, "preview-content")
        assert project_name in preview_content.text
        assert "Feasibility Score" in preview_content.text
        
        # Close preview
        driver.find_element(By.CSS_SELECTOR, "#report-preview-modal .close-button").click()
        
        # Test batch download
        checkboxes = driver.find_elements(
            By.CSS_SELECTOR, "#reports-history-table .report-checkbox"
        )
        for i in range(min(2, len(checkboxes))):
            checkboxes[i].click()
        
        driver.find_element(By.ID, "batch-download-button").click()
        
        # Verify batch download started
        batch_success = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "batch-download-success"))
        )
        assert "downloads started" in batch_success.text.lower()


def test_performance_and_concurrent_users(driver, login):
    """
    Additional test for performance under load
    Tests system behavior with multiple concurrent assessments
    """
    import threading
    import queue
    
    results_queue = queue.Queue()
    
    def create_assessment(assessment_num):
        """Create an assessment in a separate thread"""
        try:
            # Each thread needs its own driver instance for true concurrency
            thread_driver = webdriver.Chrome()
            thread_driver.get("http://localhost:8000/login")
            
            # Login
            thread_driver.find_element(By.ID, "username").send_keys(
                f"testuser{assessment_num}@example.com"
            )
            thread_driver.find_element(By.ID, "password").send_keys("TestPassword123!")
            thread_driver.find_element(By.ID, "login-button").click()
            
            # Navigate to tool
            thread_driver.get("http://localhost:8000/feasibility-tool")
            
            # Create assessment
            start_time = time.time()
            
            thread_driver.find_element(By.ID, "project-name").send_keys(
                f"Concurrent Test {assessment_num}"
            )
            thread_driver.find_element(By.ID, "project-description").send_keys(
                "Concurrent testing"
            )
            Select(thread_driver.find_element(By.ID, "project-type")).select_by_value(
                "software-development"
            )
            thread_driver.find_element(By.ID, "estimated-budget").send_keys("100000")
            # ... fill other required fields ...
            
            thread_driver.find_element(By.ID, "submit-assessment").click()
            
            # Wait for results
            WebDriverWait(thread_driver, 30).until(
                EC.presence_of_element_located((By.ID, "assessment-results"))
            )
            
            end_time = time.time()
            results_queue.put({
                "assessment_num": assessment_num,
                "duration": end_time - start_time,
                "success": True
            })
            
            thread_driver.quit()
            
        except Exception as e:
            results_queue.put({
                "assessment_num": assessment_num,
                "error": str(e),
                "success": False
            })
    
    # Create multiple threads
    threads = []
    num_concurrent = 5
    
    for i in range(num_concurrent):
        thread = threading.Thread(target=create_assessment, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join(timeout=60)
    
    # Analyze results
    results = []
    while not results_queue.empty():
        results.append(results_queue.get())
    
    # Verify all assessments completed
    successful = [r for r in results if r["success"]]
    assert len(successful) >= num_concurrent * 0.8  # At least 80% success rate
    
    # Check performance
    avg_duration = sum(r["duration"] for r in successful) / len(successful)
    assert avg_duration < 20  # Should complete within 20 seconds on average


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])