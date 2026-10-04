<?php

namespace App\Http\Controllers;

use App\Models\Review;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;
use Illuminate\View\View;

class ReviewController extends Controller
{
    public function index(): View
    {
        return view('reviews', [
            'reviews' => Review::orderByDesc('created_at')->orderByDesc('id')->get(),
            'version' => env('APP_VERSION', 'dev'),
        ]);
    }

    public function store(Request $request): RedirectResponse
    {
        $data = $request->validate([
            'book_title' => ['required', 'string', 'max:200'],
            'reviewer' => ['required', 'string', 'max:100'],
            'rating' => ['required', 'integer', 'between:1,5'],
            'comment' => ['nullable', 'string', 'max:2000'],
        ]);
        $review = Review::create($data);
        Log::info('review stored', ['id' => $review->id, 'book_title' => $review->book_title]);

        return redirect('/')->with('status', 'Thank you! Your review was saved.');
    }
}
