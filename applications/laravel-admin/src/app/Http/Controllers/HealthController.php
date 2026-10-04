<?php

namespace App\Http\Controllers;

use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\DB;
use Throwable;

class HealthController extends Controller
{
    private function base(): array
    {
        return ['service' => 'laravel-admin', 'version' => env('APP_VERSION', 'dev')];
    }

    // Liveness: PHP and Laravel answer. Deliberately no database check: a database outage must not make
    // Kubernetes restart this container (that would not fix the database).
    public function health(): JsonResponse
    {
        return response()->json(['status' => 'ok'] + $this->base());
    }

    // Readiness: can this instance do useful work right now? Only when the database answers.
    public function ready(): JsonResponse
    {
        try {
            DB::select('select 1');
        } catch (Throwable $e) {
            return response()->json(['status' => 'not ready', 'reason' => 'database: '.class_basename($e)] + $this->base(), 503);
        }

        return response()->json(['status' => 'ready'] + $this->base());
    }

    public function info(): JsonResponse
    {
        return response()->json($this->base() + [
            'language' => 'PHP',
            'runtime' => 'PHP '.PHP_VERSION.' (FPM), Laravel '.app()->version(),
            'description' => 'Book reviews: list and add reviews (server-rendered HTML)',
        ]);
    }
}
