#!/usr/bin/env python3
"""
Benchmark datasets for evaluating GLCS contradiction detection
For use in research paper evaluation section
"""

# Dataset 1: Job Role Contradictions (Simple)
JOB_ROLE_DATASET = {
    'name': 'Job Role Contradictions',
    'description': 'Tests mutual exclusivity of job roles',
    'test_cases': [
        {
            'id': 1,
            'setup': ['John is a manager'],
            'test': 'John is an engineer',
            'expected': 'contradiction',
            'category': 'mutual_exclusivity'
        },
        {
            'id': 2,
            'setup': ['Alice is a developer'],
            'test': 'Alice is a designer',
            'expected': 'contradiction',
            'category': 'mutual_exclusivity'
        },
        {
            'id': 3,
            'setup': ['Bob is an analyst'],
            'test': 'Bob is an analyst',
            'expected': 'consistent',
            'category': 'duplicate'
        },
    ]
}

# Dataset 2: Capability Contradictions (Direct Negation)
CAPABILITY_DATASET = {
    'name': 'Capability Contradictions',
    'description': 'Tests direct negation (can vs cannot)',
    'test_cases': [
        {
            'id': 1,
            'setup': ['Alice can code'],
            'test': 'Alice cannot code',
            'expected': 'contradiction',
            'category': 'direct_negation'
        },
        {
            'id': 2,
            'setup': ['Bob cannot swim'],
            'test': 'Bob can swim',
            'expected': 'contradiction',
            'category': 'direct_negation'
        },
        {
            'id': 3,
            'setup': ['Charlie can dance'],
            'test': 'Charlie can sing',
            'expected': 'consistent',
            'category': 'independent_capabilities'
        },
    ]
}

# Dataset 3: Universal Rule Violations
UNIVERSAL_RULE_DATASET = {
    'name': 'Universal Rule Violations',
    'description': 'Tests universal statements against specific instances',
    'test_cases': [
        {
            'id': 1,
            'setup': ['All birds can fly'],
            'test': 'Penguin cannot fly',
            'expected': 'contradiction',
            'category': 'universal_violation'
        },
        {
            'id': 2,
            'setup': ['No employees can access admin panel'],
            'test': 'John can access admin panel',
            'expected': 'contradiction',
            'category': 'universal_violation'
        },
        {
            'id': 3,
            'setup': ['Everyone must attend the meeting'],
            'test': 'Bob will attend the meeting',
            'expected': 'consistent',
            'category': 'universal_compliance'
        },
    ]
}

# Dataset 4: Conditional Logic
CONDITIONAL_DATASET = {
    'name': 'Conditional Logic',
    'description': 'Tests if-then reasoning',
    'test_cases': [
        {
            'id': 1,
            'setup': ['If it rains then I will stay home', 'It is raining'],
            'test': 'I will go outside',
            'expected': 'contradiction',
            'category': 'conditional_violation'
        },
        {
            'id': 2,
            'setup': ['If Alice submits report then project continues'],
            'test': 'Alice submits report',
            'expected': 'consistent',
            'category': 'conditional_antecedent'
        },
    ]
}

# Dataset 5: Complex Multi-Statement (Challenging)
COMPLEX_DATASET = {
    'name': 'Complex Multi-Statement',
    'description': 'Tests multi-hop reasoning (expected to fail - system limitation)',
    'test_cases': [
        {
            'id': 1,
            'setup': [
                'John is a manager',
                'All managers can approve budgets',
            ],
            'test': 'John cannot approve budgets',
            'expected': 'contradiction',
            'category': 'multi_hop_reasoning',
            'note': 'Requires transitive reasoning - current limitation'
        },
        {
            'id': 2,
            'setup': [
                'Alice reports to Bob',
                'Bob reports to Charlie',
            ],
            'test': 'Charlie reports to Alice',
            'expected': 'contradiction',
            'category': 'transitive_relationships',
            'note': 'Requires graph reasoning - current limitation'
        },
    ]
}

# Dataset 6: New Pattern Coverage (From Option 3)
NEW_PATTERN_DATASET = {
    'name': 'New Pattern Coverage',
    'description': 'Tests newly added patterns from Option 3',
    'test_cases': [
        {
            'id': 1,
            'setup': ['Everyone is welcome'],
            'test': 'John is not welcome',
            'expected': 'contradiction',
            'category': 'universal_everyone'
        },
        {
            'id': 2,
            'setup': ['Nobody can access the vault'],
            'test': 'Alice can access the vault',
            'expected': 'contradiction',
            'category': 'universal_nobody'
        },
        {
            'id': 3,
            'setup': ['Only admins can delete files'],
            'test': 'Users can delete files',
            'expected': 'contradiction',
            'category': 'exclusive_permission'
        },
        {
            'id': 4,
            'setup': ['Alice must approve the request'],
            'test': 'Alice will approve the request',
            'expected': 'consistent',
            'category': 'modal_verbs'
        },
    ]
}

ALL_DATASETS = [
    JOB_ROLE_DATASET,
    CAPABILITY_DATASET,
    UNIVERSAL_RULE_DATASET,
    CONDITIONAL_DATASET,
    NEW_PATTERN_DATASET,
    COMPLEX_DATASET,  # Include to document limitations
]

def get_total_test_cases():
    """Count total test cases across all datasets"""
    total = sum(len(dataset['test_cases']) for dataset in ALL_DATASETS)
    return total

def get_dataset_by_name(name):
    """Retrieve a specific dataset by name"""
    for dataset in ALL_DATASETS:
        if dataset['name'] == name:
            return dataset
    return None

if __name__ == "__main__":
    print(f"Total benchmark datasets: {len(ALL_DATASETS)}")
    print(f"Total test cases: {get_total_test_cases()}")
    print("\nDatasets:")
    for dataset in ALL_DATASETS:
        print(f"  - {dataset['name']}: {len(dataset['test_cases'])} cases")
