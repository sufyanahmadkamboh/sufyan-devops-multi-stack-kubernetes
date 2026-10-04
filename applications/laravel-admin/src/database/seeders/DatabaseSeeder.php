<?php

namespace Database\Seeders;

use App\Models\Review;
use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    /**
     * A few example reviews, added only once (running the seeder again does not duplicate them).
     */
    public function run(): void
    {
        $reviews = [
            ['book_title' => 'The Pragmatic Programmer', 'reviewer' => 'Amira', 'rating' => 5,
                'comment' => 'Still the best book about the craft.'],
            ['book_title' => 'Kubernetes Up & Running', 'reviewer' => 'Jonas', 'rating' => 4,
                'comment' => 'Clear explanations of Pods, Services and Deployments.'],
            ['book_title' => 'Clean Code', 'reviewer' => 'Lena', 'rating' => 3,
                'comment' => 'Good ideas, some examples feel dated.'],
        ];
        foreach ($reviews as $review) {
            Review::firstOrCreate(['book_title' => $review['book_title'], 'reviewer' => $review['reviewer']], $review);
        }
    }
}
