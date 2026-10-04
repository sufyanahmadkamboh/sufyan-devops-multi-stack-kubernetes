<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Bookshop · Reviews</title>
    <link rel="stylesheet" href="/css/admin.css">
</head>
<body>
<header>
    <h1>📚 Bookshop reviews</h1>
    <p class="meta">laravel-admin {{ $version }} · PHP {{ PHP_VERSION }} · Laravel {{ app()->version() }}</p>
</header>
<main>
    @if (session('status'))
        <p class="ok">{{ session('status') }}</p>
    @endif
    @if ($errors->any())
        <ul class="err">
            @foreach ($errors->all() as $error)
                <li>{{ $error }}</li>
            @endforeach
        </ul>
    @endif

    <section>
        <h2>Add a review</h2>
        <form method="post" action="/reviews">
            @csrf
            <label>Book <input name="book_title" value="{{ old('book_title') }}" required maxlength="200"></label>
            <label>Your name <input name="reviewer" value="{{ old('reviewer') }}" required maxlength="100"></label>
            <label>Rating
                <select name="rating">
                    @for ($i = 5; $i >= 1; $i--)
                        <option value="{{ $i }}" @selected(old('rating') == $i)>{{ $i }} ★</option>
                    @endfor
                </select>
            </label>
            <label>Comment <textarea name="comment" maxlength="2000">{{ old('comment') }}</textarea></label>
            <button type="submit">Save review</button>
        </form>
    </section>

    <section>
        <h2>{{ $reviews->count() }} reviews</h2>
        <table>
            <thead><tr><th>Book</th><th>Reviewer</th><th>Rating</th><th>Comment</th><th>Added</th></tr></thead>
            <tbody>
            @foreach ($reviews as $review)
                <tr>
                    <td>{{ $review->book_title }}</td>
                    <td>{{ $review->reviewer }}</td>
                    <td>{{ str_repeat('★', $review->rating) }}</td>
                    <td>{{ $review->comment }}</td>
                    <td>{{ $review->created_at?->format('Y-m-d H:i') }}</td>
                </tr>
            @endforeach
            </tbody>
        </table>
    </section>
</main>
</body>
</html>
