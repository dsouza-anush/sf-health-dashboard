#!/usr/bin/env python3
"""
Test script for AI insights service

This script tests the AI insights endpoint directly without going through the UI.
It can be used to verify that the insights service is working properly.
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

import aiohttp
import urllib3

# Disable SSL warnings for local development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


async def test_insights_api(base_url: str, time_range: str = "week") -> Dict[str, Any]:
    """
    Test the insights API endpoint
    
    Args:
        base_url: Base URL of the application
        time_range: Time range for insights (day, week, month)
        
    Returns:
        Dict containing API response
    """
    url = f"{base_url}/api/insights/?time_range={time_range}"
    
    print(f"Testing insights API: {url}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"Error: Status {response.status}")
                error_text = await response.text()
                print(f"Response: {error_text}")
                return {"error": error_text}
            
            return await response.json()


def format_insights(insights: Dict[str, Any]) -> None:
    """
    Format and print insights in a readable way
    
    Args:
        insights: Insights response from API
    """
    print("\n===== AI INSIGHTS =====\n")
    
    # Check if this is a fallback response
    if insights.get("is_fallback"):
        print("⚠️  FALLBACK RESPONSE - AI insights unavailable")
        print(f"Reason: {insights.get('potential_issue', {}).get('description')}")
        print()
    
    # Alert Pattern
    print("🔍 ALERT PATTERN:")
    print(f"  {insights.get('alert_pattern', {}).get('title')}")
    print(f"  {insights.get('alert_pattern', {}).get('description')}")
    print()
    
    # Potential Issue
    print("⚠️  POTENTIAL ISSUE:")
    print(f"  {insights.get('potential_issue', {}).get('title')}")
    print(f"  {insights.get('potential_issue', {}).get('description')}")
    print()
    
    # Suggested Action
    print("✅ SUGGESTED ACTION:")
    print(f"  {insights.get('suggested_action', {}).get('title')}")
    print(f"  {insights.get('suggested_action', {}).get('description')}")
    print()
    
    # System Health Summary
    print("📊 SYSTEM HEALTH SUMMARY:")
    print(f"  {insights.get('system_health_summary')}")
    print()
    
    # Metadata
    generated_at = insights.get('generated_at')
    if generated_at:
        try:
            dt = datetime.fromisoformat(generated_at)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            formatted_time = generated_at
    else:
        formatted_time = "Unknown"
    
    print(f"Time Range: {insights.get('time_range', 'Unknown')}")
    print(f"Generated: {formatted_time}")
    print()


async def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description="Test the AI insights service")
    parser.add_argument("--url", "-u", 
                        default="https://sf-health-dashboard-c0d39041d119.herokuapp.com",
                        help="Base URL of the application")
    parser.add_argument("--time-range", "-t", 
                        choices=["day", "week", "month"],
                        default="week",
                        help="Time range for insights")
    parser.add_argument("--raw", "-r",
                        action="store_true",
                        help="Print raw JSON response")
    
    args = parser.parse_args()
    
    try:
        insights = await test_insights_api(args.url, args.time_range)
        
        if args.raw:
            print(json.dumps(insights, indent=2))
        else:
            format_insights(insights)
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))