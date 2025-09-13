# 🎮 Test Data & Screen Recording Framework
*Leveraging Real Clash Royale Gameplay for AI Training & Testing*

## 📱 Screen Recording Collection Strategy

### Current Assets
- **Real iOS screen recordings** of Clash Royale matches
- **Authentic gameplay data** for training placement analysis AI
- **Diverse scenarios** for comprehensive testing coverage

### Recording Organization Structure
```
test-data/
├── screen-recordings/
│   ├── raw-recordings/          # Original iOS screen recordings
│   │   ├── wins/               # Winning matches
│   │   ├── losses/             # Losing matches
│   │   └── draws/              # Draw matches
│   ├── processed/              # Preprocessed for AI training
│   │   ├── frames/             # Extracted key frames
│   │   ├── annotations/        # Placement moment annotations
│   │   └── metadata/           # Match metadata (deck, result, etc.)
│   └── test-cases/             # Specific test scenarios
│       ├── perfect-placements/ # Known optimal placements
│       ├── poor-placements/    # Known suboptimal placements
│       └── edge-cases/         # Unusual game states
```

## 🔬 Testing Framework for Screen Recordings

### Phase 1: Data Preparation Pipeline
```python
# Screen Recording Processing Pipeline
class ScreenRecordingProcessor:
    def __init__(self):
        self.video_analyzer = VideoAnalyzer()
        self.frame_extractor = FrameExtractor()
        self.annotation_tool = PlacementAnnotator()
    
    def process_raw_recording(self, video_path: str):
        """
        Convert raw iOS screen recording into training/testing data
        """
        # 1. Extract video metadata
        metadata = self.video_analyzer.extract_metadata(video_path)
        
        # 2. Identify placement moments
        placement_moments = self.identify_card_placements(video_path)
        
        # 3. Extract frames at placement moments
        key_frames = []
        for moment in placement_moments:
            frame = self.frame_extractor.extract_frame(
                video_path, 
                timestamp=moment.timestamp
            )
            key_frames.append({
                'timestamp': moment.timestamp,
                'frame': frame,
                'placed_card': moment.card_id,
                'placement_coords': moment.coordinates
            })
        
        # 4. Generate training annotations
        annotations = self.annotation_tool.create_annotations(key_frames)
        
        return {
            'video_metadata': metadata,
            'placement_moments': placement_moments,
            'annotated_frames': annotations,
            'processed_data_path': self.save_processed_data(key_frames)
        }
    
    def identify_card_placements(self, video_path: str):
        """
        Automatically detect when cards are placed in the video
        """
        # Use computer vision to detect:
        # - Elixir count changes (indicates card placement)
        # - New units appearing on board
        # - Card selection in hand
        # - Placement animations
        pass
```

### Phase 2: AI Training Data Generation
```python
# Convert Screen Recordings to Training Dataset
class TrainingDataGenerator:
    def __init__(self):
        self.board_detector = GameBoardDetector()
        self.placement_evaluator = PlacementEvaluator()
    
    def create_training_dataset(self, recordings_directory: str):
        """
        Generate labeled training data from screen recordings
        """
        dataset = []
        
        for recording in self.get_recordings(recordings_directory):
            # Process each recording
            processed = self.process_recording(recording)
            
            for placement_moment in processed.placement_moments:
                # Extract game state
                game_state = self.board_detector.extract_game_state(
                    placement_moment.frame
                )
                
                # Generate optimal placement label
                optimal_placement = self.placement_evaluator.calculate_optimal(
                    card=placement_moment.card,
                    game_state=game_state
                )
                
                # Create training sample
                training_sample = {
                    'input': {
                        'frame': placement_moment.frame,
                        'game_state': game_state,
                        'card_to_place': placement_moment.card,
                        'elixir_available': placement_moment.elixir
                    },
                    'label': {
                        'optimal_placement': optimal_placement.coordinates,
                        'placement_score': optimal_placement.score,
                        'reasoning': optimal_placement.explanation
                    },
                    'metadata': {
                        'source_video': recording.path,
                        'timestamp': placement_moment.timestamp,
                        'match_outcome': recording.result
                    }
                }
                
                dataset.append(training_sample)
        
        return dataset
```

### Phase 3: Interactive Testing Framework
```python
# Test Interactive Placement Analysis with Real Data
class PlacementAnalysisTestSuite:
    def __init__(self):
        self.analyzer = InteractivePlacementAnalyzer()
        self.test_cases = self.load_test_cases()
    
    def test_with_screen_recordings(self):
        """
        Run placement analysis tests using real screen recording data
        """
        results = []
        
        for test_case in self.test_cases:
            # Test the interactive placement analysis
            analysis_result = self.analyzer.analyze_placement_moment(
                video_frame=test_case.frame,
                user_placement_coords=test_case.actual_placement
            )
            
            # Compare with expected results
            accuracy_score = self.compare_with_expected(
                analysis_result, 
                test_case.expected_analysis
            )
            
            results.append({
                'test_case': test_case.name,
                'accuracy_score': accuracy_score,
                'ai_prediction': analysis_result.placement_score,
                'expected_score': test_case.expected_score,
                'difference': abs(analysis_result.placement_score - test_case.expected_score)
            })
        
        return self.generate_test_report(results)
    
    def benchmark_analysis_speed(self):
        """
        Test analysis speed with real video frames
        """
        test_frames = self.load_test_frames()
        speed_results = []
        
        for frame in test_frames:
            start_time = time.time()
            
            result = self.analyzer.analyze_placement_moment(
                video_frame=frame.image,
                user_placement_coords=frame.placement_coords
            )
            
            end_time = time.time()
            analysis_time = (end_time - start_time) * 1000  # milliseconds
            
            speed_results.append({
                'frame_id': frame.id,
                'analysis_time_ms': analysis_time,
                'meets_target': analysis_time < 500  # Target: <500ms
            })
        
        return speed_results
```

## 🎯 Test Case Categories from Screen Recordings

### 1. Perfect Placement Scenarios
```python
perfect_placement_tests = [
    {
        'name': 'Hog Rider Bridge Placement',
        'description': 'Optimal bridge placement for Hog push',
        'expected_score': 9-10,
        'scenario': 'Counter-attack opportunity with elixir advantage'
    },
    {
        'name': 'Defensive Building Placement', 
        'description': 'Tesla placement to counter Giant push',
        'expected_score': 8-10,
        'scenario': 'Incoming heavy push, optimal defensive positioning'
    }
]
```

### 2. Poor Placement Learning Cases
```python
poor_placement_tests = [
    {
        'name': 'Overcommitted Defense',
        'description': 'Expensive defense with no counter-push potential',
        'expected_score': 2-4,
        'learning_objective': 'Teach elixir efficiency'
    },
    {
        'name': 'Premature Spell Usage',
        'description': 'Fireball used too early, missed value',
        'expected_score': 3-5,
        'learning_objective': 'Teach spell timing and value'
    }
]
```

### 3. Edge Case Scenarios
```python
edge_case_tests = [
    {
        'name': 'Overtime Pressure',
        'description': 'Critical placement in overtime with low elixir',
        'complexity': 'High',
        'context': 'Time pressure affects optimal placement calculation'
    },
    {
        'name': 'Mirror Match Dynamics',
        'description': 'Same deck vs same deck, subtle placement differences',
        'complexity': 'Expert',
        'context': 'Tests nuanced understanding of card interactions'
    }
]
```

## 📊 Testing Metrics & Validation

### AI Accuracy Validation
```python
class AccuracyValidator:
    def validate_placement_analysis(self, test_results):
        """
        Validate AI placement analysis against known good/bad placements
        """
        metrics = {
            'placement_score_accuracy': self.calculate_score_accuracy(test_results),
            'optimal_tile_accuracy': self.calculate_tile_accuracy(test_results),
            'reasoning_quality': self.evaluate_reasoning_quality(test_results),
            'confidence_calibration': self.check_confidence_calibration(test_results)
        }
        
        return metrics
    
    def calculate_score_accuracy(self, results):
        """
        How close AI scores are to expert evaluations
        """
        score_differences = []
        for result in results:
            diff = abs(result.ai_score - result.expert_score)
            score_differences.append(diff)
        
        return {
            'mean_absolute_error': np.mean(score_differences),
            'within_1_point': sum(1 for diff in score_differences if diff <= 1) / len(score_differences),
            'within_2_points': sum(1 for diff in score_differences if diff <= 2) / len(score_differences)
        }
```

### Performance Benchmarks
```python
performance_targets = {
    'analysis_speed': '<500ms per placement analysis',
    'accuracy_targets': {
        'placement_score_mae': '<1.5 points difference from expert',
        'optimal_tile_accuracy': '>80% within 2 tiles of optimal',
        'reasoning_relevance': '>85% relevant strategic insights'
    },
    'user_experience': {
        'feedback_clarity': '>90% users understand AI feedback',
        'improvement_correlation': '>70% users improve after following AI advice',
        'engagement_retention': '>60% users return next day after first analysis'
    }
}
```

## 🔧 Implementation Plan for Testing Framework

### Week 1: Data Processing Setup
```bash
# Set up processing pipeline for your screen recordings
□ Create video processing scripts for iOS recordings
□ Implement frame extraction at placement moments  
□ Build annotation tools for labeling optimal placements
□ Set up data storage structure for processed recordings
```

### Week 2: AI Training Data Generation
```bash
# Convert recordings to training data
□ Process existing screen recordings into training dataset
□ Generate placement annotations with expert evaluations
□ Create balanced dataset (good/bad/edge-case placements)
□ Implement data augmentation for varied scenarios
```

### Week 3: Testing Framework Implementation
```bash
# Build comprehensive testing system
□ Implement automated testing suite using processed data
□ Create performance benchmarking tools
□ Build accuracy validation against expert annotations
□ Set up continuous testing pipeline
```

### Week 4: Validation & Refinement
```bash
# Validate AI performance with real data
□ Run comprehensive accuracy tests
□ Benchmark analysis speed performance
□ Validate user experience with test scenarios
□ Refine AI based on testing results
```

## 💡 Leveraging Your Screen Recordings

### Immediate Value
1. **Real-world Training Data**: Your recordings provide authentic gameplay scenarios
2. **Edge Case Discovery**: Identify unusual situations that need special handling
3. **Performance Validation**: Test AI accuracy against real placements
4. **User Experience Testing**: Validate that feedback makes sense in real contexts

### Long-term Benefits
1. **Continuous Improvement**: Regular testing against new recordings
2. **Meta Adaptation**: Update AI as game meta evolves
3. **Quality Assurance**: Ensure AI maintains accuracy over time
4. **Feature Development**: Use recordings to develop new analysis features

This framework turns your screen recordings into a powerful asset for developing and validating the most accurate placement analysis system possible. The real gameplay data will be invaluable for training AI that truly understands Clash Royale strategy!
