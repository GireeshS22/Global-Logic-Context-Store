#!/usr/bin/env python3
"""
Evaluation script for GLCS research paper
Produces quantitative metrics: precision, recall, F1, accuracy
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from glcs import SimpleParser, SimpleMemory, ConsistencyChecker
from evaluation.benchmark_datasets import ALL_DATASETS
from typing import Dict, List
import json

class GLCSEvaluator:
    """Evaluates GLCS performance on benchmark datasets"""

    def __init__(self):
        self.parser = SimpleParser()
        self.results = []

    def run_test_case(self, test_case: Dict) -> Dict:
        """Run a single test case"""
        memory = SimpleMemory()
        checker = ConsistencyChecker(memory)

        # Setup: Store initial statements
        setup_success = True
        for stmt_text in test_case['setup']:
            stmt = self.parser.parse(stmt_text)
            if stmt:
                memory.store(stmt)
            else:
                setup_success = False

        # Test: Check the test statement
        test_text = test_case['test']
        test_stmt = self.parser.parse(test_text)

        if not test_stmt:
            return {
                'test_case_id': test_case['id'],
                'category': test_case['category'],
                'expected': test_case['expected'],
                'actual': 'parse_failed',
                'correct': False,
                'setup_success': setup_success,
                'note': test_case.get('note', '')
            }

        is_consistent, confidence, violations = checker.check_consistency(test_stmt)

        # Determine actual result
        if is_consistent:
            actual = 'consistent'
        else:
            actual = 'contradiction'

        # Check if correct
        correct = (actual == test_case['expected'])

        return {
            'test_case_id': test_case['id'],
            'category': test_case['category'],
            'expected': test_case['expected'],
            'actual': actual,
            'correct': correct,
            'confidence': confidence,
            'violations': len(violations),
            'setup_success': setup_success,
            'note': test_case.get('note', '')
        }

    def evaluate_dataset(self, dataset: Dict) -> Dict:
        """Evaluate all test cases in a dataset"""
        print(f"\n{'='*70}")
        print(f"Evaluating: {dataset['name']}")
        print(f"Description: {dataset['description']}")
        print(f"{'='*70}")

        results = []
        for test_case in dataset['test_cases']:
            result = self.run_test_case(test_case)
            results.append(result)

            # Print individual result
            status = "✅" if result['correct'] else "❌"
            print(f"{status} Case {result['test_case_id']}: {result['category']}")
            print(f"   Expected: {result['expected']}, Got: {result['actual']}")
            if result['note']:
                print(f"   Note: {result['note']}")

        # Calculate metrics
        total = len(results)
        correct = sum(1 for r in results if r['correct'])
        accuracy = correct / total if total > 0 else 0

        # Count by type for confusion matrix
        tp = sum(1 for r in results if r['expected'] == 'contradiction' and r['actual'] == 'contradiction')
        fp = sum(1 for r in results if r['expected'] == 'consistent' and r['actual'] == 'contradiction')
        tn = sum(1 for r in results if r['expected'] == 'consistent' and r['actual'] == 'consistent')
        fn = sum(1 for r in results if r['expected'] == 'contradiction' and r['actual'] == 'consistent')
        parse_failed = sum(1 for r in results if r['actual'] == 'parse_failed')

        # Calculate precision, recall, F1
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        metrics = {
            'dataset_name': dataset['name'],
            'total_cases': total,
            'correct': correct,
            'accuracy': accuracy,
            'true_positives': tp,
            'false_positives': fp,
            'true_negatives': tn,
            'false_negatives': fn,
            'parse_failures': parse_failed,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'results': results
        }

        # Print summary
        print(f"\n📊 Results:")
        print(f"   Accuracy: {accuracy:.2%} ({correct}/{total})")
        print(f"   Precision: {precision:.2%}")
        print(f"   Recall: {recall:.2%}")
        print(f"   F1 Score: {f1:.2%}")
        if parse_failed > 0:
            print(f"   ⚠️  Parse failures: {parse_failed}/{total}")

        return metrics

    def evaluate_all(self) -> Dict:
        """Evaluate all datasets"""
        all_metrics = []

        for dataset in ALL_DATASETS:
            metrics = self.evaluate_dataset(dataset)
            all_metrics.append(metrics)

        # Calculate overall metrics
        total_cases = sum(m['total_cases'] for m in all_metrics)
        total_correct = sum(m['correct'] for m in all_metrics)
        overall_accuracy = total_correct / total_cases if total_cases > 0 else 0

        total_tp = sum(m['true_positives'] for m in all_metrics)
        total_fp = sum(m['false_positives'] for m in all_metrics)
        total_tn = sum(m['true_negatives'] for m in all_metrics)
        total_fn = sum(m['false_negatives'] for m in all_metrics)

        overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        overall_f1 = 2 * (overall_precision * overall_recall) / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0

        overall = {
            'total_cases': total_cases,
            'total_correct': total_correct,
            'overall_accuracy': overall_accuracy,
            'overall_precision': overall_precision,
            'overall_recall': overall_recall,
            'overall_f1': overall_f1,
            'dataset_metrics': all_metrics
        }

        # Print overall summary
        print(f"\n{'='*70}")
        print(f"OVERALL RESULTS")
        print(f"{'='*70}")
        print(f"Total Test Cases: {total_cases}")
        print(f"Overall Accuracy: {overall_accuracy:.2%} ({total_correct}/{total_cases})")
        print(f"Overall Precision: {overall_precision:.2%}")
        print(f"Overall Recall: {overall_recall:.2%}")
        print(f"Overall F1 Score: {overall_f1:.2%}")
        print(f"\nConfusion Matrix:")
        print(f"  True Positives:  {total_tp}")
        print(f"  False Positives: {total_fp}")
        print(f"  True Negatives:  {total_tn}")
        print(f"  False Negatives: {total_fn}")

        return overall

    def save_results(self, results: Dict, output_file: str = "evaluation_results.json"):
        """Save results to JSON file for paper"""
        output_path = os.path.join(os.path.dirname(__file__), output_file)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {output_path}")

def main():
    evaluator = GLCSEvaluator()
    results = evaluator.evaluate_all()
    evaluator.save_results(results)

    print("\n" + "="*70)
    print("RECOMMENDATIONS FOR PAPER:")
    print("="*70)
    print("1. Present overall metrics in abstract/introduction")
    print("2. Break down by dataset category in results section")
    print("3. Discuss failures in limitations section")
    print("4. Compare with baseline (keyword matching, simple rules)")
    print("5. Include confusion matrix visualization")
    print("6. Highlight what works well vs limitations")

if __name__ == "__main__":
    main()
