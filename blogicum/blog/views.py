from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy, reverse
from django.db.models.functions import Now
import datetime as dt

from django.conf import settings
from blog.models import Category, Post, Comment
from blog.forms import PostForm, CommentForm, UserUpdateForm


User = get_user_model()


class PostListView(ListView):
    model = Post
    queryset = Post.objects.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=dt.datetime.now(tz=dt.timezone(dt.timedelta())),
    )
    ordering = ('-pub_date')
    paginate_by = settings.POSTS_PER_PAGE
    template_name = 'blog/index.html'


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    ordering = ('-pub_date')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        username = self.request.user
        return reverse('blog:profile', kwargs={'username': username})


class PostDetailView(DetailView):
    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/detail.html'

    def get_object(self, **kwargs):
        object = super(PostDetailView, self).get_object()
        if self.request.user != object.author:
            object = get_object_or_404(
                Post,
                is_published=True,
                category__is_published=True,
                id=self.kwargs['post_id'],
            )
        return object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('post',)
        )
        return context


class PostUpdateView(UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, id=self.kwargs['post_id'])
        if instance.author != request.user:
            return redirect(
                reverse_lazy(
                    'blog:post_detail',
                    kwargs={'post_id': self.kwargs['post_id']},
                ),
            )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save()
        return redirect('blog:post_detail', self.kwargs['post_id'])


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, id=self.kwargs['post_id'])
        if instance.author != request.user:
            return redirect(
                reverse_lazy(
                    'blog:post_detail',
                    kwargs={'post_id': self.kwargs['post_id']},
                ),
            )
        return super().dispatch(request, *args, **kwargs)


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    paginate_by = settings.POSTS_PER_PAGE
    template_name = 'blog/category.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True,
        )
        return context

    def get_queryset(self):
        return Post.objects.filter(
            pub_date__lte=Now(),
            category__slug=self.kwargs['category_slug'],
            is_published=True,
        )


class ProfileListView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = settings.POSTS_PER_PAGE

    def get_queryset(self):
        self.user = get_object_or_404(User, username=self.kwargs['username'])
        return Post.objects.filter(author=self.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.user
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        username = self.request.user
        return reverse('blog:profile', kwargs={'username': username})


class CommentCreateView(LoginRequiredMixin, CreateView):
    comment_post = None
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post,
            id=self.kwargs['post_id']
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(
            Comment,
            id=self.kwargs['comment_id'],
            post__id=kwargs['post_id'],
        )
        if instance.author != request.user:
            return redirect(
                reverse_lazy(
                    'blog:post_detail',
                    kwargs={'post_id': self.kwargs['post_id']},
                ),
            )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post,
            id=self.kwargs['post_id']
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.kwargs['post_id']})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(
            Comment,
            id=self.kwargs['comment_id'],
            post__id=kwargs['post_id'],
        )
        if instance.author != request.user:
            return redirect(
                reverse_lazy(
                    'blog:post_detail',
                    kwargs={'post_id': self.kwargs['post_id']},
                ),
            )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )
